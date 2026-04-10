from odoo import models, fields, api
from odoo.exceptions import UserError

class DonHang(models.Model):
    _name = 'quan_ly_don_hang.don_hang'
    _description = 'Quản lý đơn hàng'
    _rec_name = 'ma_don'

    ma_don = fields.Char(string="Mã đơn hàng", default="Mới", readonly=True)
    ngay_tao = fields.Datetime(string="Ngày tạo", default=fields.Datetime.now)
    
    # Kết nối master data từ thien_thoi_base
    khach_hang_id = fields.Many2one('thien_thoi_base.khach_hang', string="Khách hàng", required=True)
    nhan_vien_id = fields.Many2one('res.users', string="Nhân viên xử lý", default=lambda self: self.env.user)
    
    trang_thai = fields.Selection([
        ('nhap', 'Mới (Nháp)'),
        ('xac_nhan', 'Đã xác nhận'),
        ('dong_goi', 'Đang đóng gói'),
        ('xuat_kho', 'Đã xuất kho'),
        ('huy', 'Đã hủy')
    ], string="Trạng thái", default='nhap')
    loai_khach_hang = fields.Selection([
        ('le', 'Khách lẻ'),
        ('si', 'Khách sỉ')
    ], string="Loại khách hàng", default='le', required=True)
    chi_tiet_don_ids = fields.One2many('quan_ly_don_hang.chi_tiet', 'don_hang_id', string="Sản phẩm")
    tong_tien = fields.Float(string="Tổng cộng", compute="_compute_tong_tien", store=True)

    @api.depends('chi_tiet_don_ids.thanh_tien')
    def _compute_tong_tien(self):
        for record in self:
            record.tong_tien = sum(line.thanh_tien for line in record.chi_tiet_don_ids)

    def action_confirm(self):
        for record in self:
            if not record.chi_tiet_don_ids:
                raise UserError("Vui lòng chọn sản phẩm trước khi xác nhận!")
            record.ma_don = self.env['ir.sequence'].next_by_code('quan_ly_don_hang.order.seq') or 'DH001'
            record.trang_thai = 'xac_nhan'

    def action_pack(self):
        self.write({'trang_thai': 'dong_goi'})

    def action_done(self):
        """Xử lý xuất kho: Trừ tồn kho tương tự quan_ly_nhap"""
        for record in self:
            for line in record.chi_tiet_don_ids:
                # Tìm tồn kho tại kho mặc định (hoặc thêm trường kho_id vào đơn hàng)
                ton_kho = self.env['thien_thoi_base.ton_kho'].search([
                    ('san_pham_id', '=', line.san_pham_id.id)
                ], limit=1)
                
                if not ton_kho or ton_kho.so_luong_hien_tai < line.so_luong:
                    raise UserError(f"Sản phẩm {line.san_pham_id.ten_sp} không đủ tồn kho để xuất!")
                
                ton_kho.so_luong_hien_tai -= line.so_luong
            record.trang_thai = 'xuat_kho'

    def action_cancel(self):
        self.write({'trang_thai': 'huy'})

class ChiTietDonHang(models.Model):
    _name = 'quan_ly_don_hang.chi_tiet'
    _description = 'Chi tiết đơn hàng'

    don_hang_id = fields.Many2one('quan_ly_don_hang.don_hang', ondelete='cascade')
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string="Sản phẩm", required=True)
    so_luong = fields.Float(string="Số lượng", default=1.0)
    don_gia = fields.Float(string="Đơn giá", related="san_pham_id.gia_ban", readonly=False)
    thanh_tien = fields.Float(string="Thành tiền", compute="_compute_thanh_tien")

    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for line in self:
            line.thanh_tien = line.so_luong * line.don_gia