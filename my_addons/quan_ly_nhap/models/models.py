from odoo import models, fields, api
from datetime import datetime

class PhieuNhapKho(models.Model):
    _name = 'quan_ly_nhap.phieu_nhap'
    _description = 'Phiếu Nhập Kho Thiên Thời'
    _order = 'ngay_nhap desc'

    name = fields.Char(string='Mã Phiếu', required=True, copy=False, readonly=True, default='Mới')
    ngay_nhap = fields.Datetime(string='Ngày Nhập', default=fields.Datetime.now)
    nha_cung_cap_id = fields.Many2one('res.partner', string='Nhà Cung Cấp', required=True)
    nhan_vien_id = fields.Many2one('res.users', string='Nhân Viên Tiếp Nhận', default=lambda self: self.env.user)
    
    line_ids = fields.One2many('quan_ly_nhap.chi_tiet_nhap', 'phieu_id', string='Chi Tiết Nhập')
    
    tong_gia_tri = fields.Float(string='Tổng Giá Trị (VNĐ)', compute='_compute_tong_tien', store=True)
    trang_thai = fields.Selection([
        ('du_thao', 'Dự Thảo'),
        ('da_xac_nhan', 'Đã Nhập Kho'),
        ('tra_hang', 'Đã Trả Hàng')
    ], string='Trạng Thái', default='du_thao')

    @api.depends('line_ids.thanh_tien')
    def _compute_tong_tien(self):
        for record in self:
            record.tong_gia_tri = sum(line.thanh_tien for line in record.line_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', 'Mới') == 'Mới':
            vals['name'] = self.env['ir.sequence'].next_by_code('quan_ly_nhap.phieu_nhap') or 'PNK/' + datetime.now().strftime('%Y/%m/%d/%H%M')
        return super(PhieuNhapKho, self).create(vals)

    def action_confirm(self):
        self.trang_thai = 'da_xac_nhan'

class ChiTietNhap(models.Model):
    _name = 'quan_ly_nhap.chi_tiet_nhap'
    _description = 'Chi Tiết Nhập Kho'

    phieu_id = fields.Many2one('quan_ly_nhap.phieu_nhap', string='Phiếu Nhập', ondelete='cascade')
    san_pham_id = fields.Many2one('product.product', string='Sản Phẩm', required=True)
    
    so_luong_nhap = fields.Float(string='Số Lượng (kg)', default=1.0)
    don_gia = fields.Float(string='Đơn Giá')
    thanh_tien = fields.Float(string='Thành Tiền', compute='_compute_thanh_tien', store=True)
    
    chat_luong = fields.Selection([
        ('tot', 'Đạt chất lượng'),
        ('loi_nhe', 'Lỗi nhẹ (Chấp nhận)'),
        ('loi_nang', 'Lỗi nặng (Trả hàng)')
    ], string='Đánh giá chất lượng', default='tot')

    ma_lo = fields.Char(string='Mã Số Lô', help="Định dạng: YYMMDD-Vendor-Product")

    @api.depends('so_luong_nhap', 'don_gia')
    def _compute_thanh_tien(self):
        for line in self:
            line.thanh_tien = line.so_luong_nhap * line.don_gia

    @api.onchange('san_pham_id', 'phieu_id.nha_cung_cap_id')
    def _onchange_generate_lot(self):
        """Tự động gợi ý mã lô khi chọn sản phẩm"""
        if self.san_pham_id and self.phieu_id.nha_cung_cap_id:
            date_str = datetime.now().strftime('%y%m%d')
            vendor_code = (self.phieu_id.nha_cung_cap_id.name[:3]).upper()
            product_code = (self.san_pham_id.name[:3]).upper()
            self.ma_lo = f"{date_str}-{vendor_code}-{product_code}"