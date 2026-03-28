from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template' # Kế thừa bảng Sản phẩm gốc

    # Chỉ thêm những gì Thiên Thời cần mà Odoo chưa có
    loai_san_pham_thien_thoi = fields.Selection([
        ('thô', 'Nguyên liệu (Bánh phôi)'),
        ('hoàn chỉnh', 'Thành phẩm (Đóng gói)')
    ], string="Loại Sản Phẩm", default='thô')