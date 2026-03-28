from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner' # Kế thừa bảng đối tác của Odoo

    # Thêm trường phân loại để lọc cho Nhập/Xuất kho
    loai_doi_tac = fields.Selection([
        ('khach_hang', 'Khách hàng (Mua bánh)'),
        ('nha_cung_cap', 'Nhà cung cấp (Bán phôi/Gia vị)'),
        ('ca_hai', 'Vừa là khách vừa là nhà cung cấp')
    ], string="Phân loại Đối tác", default='khach_hang')
    
    ma_doi_tac_thien_thoi = fields.Char(string="Mã Đối Tác Riêng")