from odoo import models, fields

class ThienThoiProduct(models.Model):
    _name = 'thien_thoi.product'
    _description = 'Sản phẩm Thiên Thời'

    # Các thuộc tính dựa trên Class Diagram
    name = fields.Char(string='Tên sản phẩm', required=True)
    default_code = fields.Char(string='Mã nội bộ (SKU)')
    product_type = fields.Selection([
        ('raw_material', 'Nguyên liệu (Bánh phôi/Gia vị)'),
        ('finished_product', 'Thành phẩm (Bánh tráng trộn)'),
        ('packaging', 'Bao bì')
    ], string='Loại sản phẩm', default='raw_material')
    
    uom_id = fields.Char(string='Đơn vị tính', default='kg') # Thiên Thời tính theo kg
    list_price = fields.Float(string='Giá bán Niêm yết')
    standard_price = fields.Float(string='Giá vốn ước tính')
    
    description = fields.Text(string='Mô tả sản phẩm')