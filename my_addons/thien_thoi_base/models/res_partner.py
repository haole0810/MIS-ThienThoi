from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection([
        ('supplier', 'Nhà cung cấp'),
        ('customer', 'Khách hàng lẻ'),
        ('wholesaler', 'Khách sỉ')
    ], string='Phân loại đối tác', default='supplier')
    
    # name, phone, email, street đã có sẵn trong res.partner gốc, không cần khai báo lại
    comment_thien_thoi = fields.Text(string='Ghi chú nghiệp vụ')