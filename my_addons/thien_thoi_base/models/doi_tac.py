from odoo import models, fields

class KhachHang(models.Model):
    _name = 'thien_thoi_base.khach_hang'
    _description = 'Danh mục Khách hàng'
    _rec_name = 'ten_kh'

    ma_kh = fields.Char(string="Mã khách hàng")
    ten_kh = fields.Char(string="Tên khách hàng", required=True)
    so_dien_thoai = fields.Char(string="Số điện thoại")
    dia_chi = fields.Char(string="Địa chỉ")

class NhaCungCap(models.Model):
    _name = 'thien_thoi_base.nha_cung_cap'
    _description = 'Danh mục Nhà cung cấp'
    _rec_name = 'ten_ncc'

    ma_ncc = fields.Char(string="Mã NCC")
    ten_ncc = fields.Char(string="Tên Nhà cung cấp", required=True)
    so_dien_thoai = fields.Char(string="Số điện thoại")
    dia_chi = fields.Char(string="Địa chỉ")