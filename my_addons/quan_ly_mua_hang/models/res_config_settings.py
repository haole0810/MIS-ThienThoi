from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Lưu email và mật khẩu vào hệ thống
    purchase_sender_email = fields.Char(
        string="Email gửi đi", 
        config_parameter='quan_ly_mua_hang.sender_email'
    )
    purchase_sender_password = fields.Char(
        string="Mật khẩu ứng dụng", 
        config_parameter='quan_ly_mua_hang.sender_password'
    )