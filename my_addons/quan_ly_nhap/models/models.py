from odoo import models, fields, api
from odoo.exceptions import UserError

class Kho(models.Model):
    _name = 'quan_ly_nhap.kho'
    _description = 'Quản lý danh mục Kho'
    _rec_name = 'ten_kho'

    ma_kho = fields.Char(string="Mã kho")
    ten_kho = fields.Char(string="Tên kho")
    dia_diem = fields.Char(string="Địa điểm")
    suc_chua = fields.Integer(string="Sức chứa")

class TonKho(models.Model):
    _name = 'quan_ly_nhap.ton_kho'
    _description = 'Quản lý Tồn Kho'
    _rec_name = 'ma_ton_kho'

    ma_ton_kho = fields.Char(string="Mã tồn kho")
    so_luong_hien_tai = fields.Float(string="Số lượng hiện tại", default=0.0)
    muc_toi_thieu = fields.Float(string="Mức tối thiểu")
    ngay_cap_nhat = fields.Date(string="Ngày cập nhật", default=fields.Date.context_today)

    san_pham_id = fields.Many2one('product.product', string="Sản phẩm")
    kho_id = fields.Many2one('quan_ly_nhap.kho', string="Kho")

class ChiTietNhap(models.Model):
    _name = 'quan_ly_nhap.chi_tiet_nhap'
    _description = 'Chi Tiết Phiếu Nhập'

    so_luong_nhap = fields.Float(string="Số lượng nhập", required=True, default=1.0)
    don_gia = fields.Float(string="Đơn giá")
    chat_luong = fields.Selection([
        ('tot', 'Tốt'),
        ('loi', 'Lỗi')
    ], string="Chất lượng")

    phieu_nhap_id = fields.Many2one('quan_ly_nhap.phieu_nhap', string="Phiếu nhập", ondelete='cascade')
    san_pham_id = fields.Many2one('product.product', string="Sản phẩm", required=True)

class PhieuNhapKho(models.Model):
    _name = 'quan_ly_nhap.phieu_nhap'
    _description = 'Phiếu Nhập Kho'
    _rec_name = 'ma_phieu'
    _order = 'ngay_nhap desc'

    ma_phieu = fields.Char(string="Mã phiếu", default="Mới")
    ngay_nhap = fields.Datetime(string="Ngày nhập", default=fields.Datetime.now)
    tong_gia_tri = fields.Float(string="Tổng giá trị", compute='_compute_tong_tien', store=True)
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('da_xac_nhan', 'Đã xác nhận')
    ], string="Trạng thái", default='nhap')

    chi_tiet_nhap_ids = fields.One2many('quan_ly_nhap.chi_tiet_nhap', 'phieu_nhap_id', string="Chi tiết nhập")
    nha_cung_cap_id = fields.Many2one('res.partner', string="Nhà cung cấp", required=True)
    nguoi_dung_id = fields.Many2one('res.users', string="Người dùng", default=lambda self: self.env.user)
    
    kho_id = fields.Many2one('quan_ly_nhap.kho', string="Nhập vào Kho", required=True)

    @api.depends('chi_tiet_nhap_ids.so_luong_nhap', 'chi_tiet_nhap_ids.don_gia')
    def _compute_tong_tien(self):
        for phieu in self:
            phieu.tong_gia_tri = sum((line.so_luong_nhap * line.don_gia) for line in phieu.chi_tiet_nhap_ids)

    def xacNhan(self):
        for phieu in self:
            if not phieu.chi_tiet_nhap_ids:
                raise UserError("Phải có ít nhất 1 sản phẩm để nhập kho!")

            for chi_tiet in phieu.chi_tiet_nhap_ids:
                ton_kho = self.env['quan_ly_nhap.ton_kho'].search([
                    ('san_pham_id', '=', chi_tiet.san_pham_id.id),
                    ('kho_id', '=', phieu.kho_id.id)
                ], limit=1)

                if ton_kho:
                    ton_kho.so_luong_hien_tai += chi_tiet.so_luong_nhap
                    ton_kho.ngay_cap_nhat = fields.Date.context_today(self)
                else:
                    self.env['quan_ly_nhap.ton_kho'].create({
                        'ma_ton_kho': f"TK-{chi_tiet.san_pham_id.id}-{phieu.kho_id.id}",
                        'san_pham_id': chi_tiet.san_pham_id.id,
                        'kho_id': phieu.kho_id.id,
                        'so_luong_hien_tai': chi_tiet.so_luong_nhap,
                    })

            phieu.trang_thai = 'da_xac_nhan'