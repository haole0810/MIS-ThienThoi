from odoo import models, fields

class SanPham(models.Model):
    _name = 'thien_thoi_base.san_pham'
    _description = 'Danh mục Sản phẩm & Nguyên liệu'
    _rec_name = 'ten_sp'

    ma_sp = fields.Char(string="Mã sản phẩm", required=True)
    ten_sp = fields.Char(string="Tên sản phẩm", required=True)
    loai_sp = fields.Selection([
        ('banh_phoi', 'Bánh phôi'),
        ('gia_vi', 'Gia vị'),
        ('bao_bi', 'Bao bì'),
        ('thanh_pham', 'Thành phẩm')
    ], string="Loại sản phẩm", required=True)
    don_vi_tinh = fields.Char(string="Đơn vị tính", default="kg")
    gia_ban = fields.Float(string="Giá bán tiêu chuẩn")
    mo_ta = fields.Text(string="Mô tả thêm")