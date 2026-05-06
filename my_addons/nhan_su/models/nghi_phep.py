from odoo import models, fields, api

class NghiPhep(models.Model):
    _name = 'nhan_su.nghi_phep'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Nghỉ phép'

    nhan_vien_id = fields.Many2one('nhan_su.nhan_vien', string='Nhân viên', required=True, tracking=True)
    ngay_nghi = fields.Date(string='Ngày nghỉ', default=fields.Date.today(), required=True, tracking=True)
    
    loai_nghi = fields.Selection([
        ('phep', 'Nghỉ có phép'),
        ('khong_phep', 'Nghỉ không phép'),
  
    ], string='Loại nghỉ', default='phep', required=True, tracking=True)
    
    ly_do = fields.Text(string='Lý do nghỉ')
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirm', 'Chờ duyệt'),
        ('validate', 'Đã duyệt'),
        ('refuse', 'Từ chối')
    ], string='Trạng thái', default='draft', tracking=True)

    def action_confirm(self):
        self.state = 'confirm'

    def action_validate(self):
        self.state = 'validate'
        self.env['tinh_luong.bang_luong']._recompute_employee_payrolls(
            self.nhan_vien_id,
            self.ngay_nghi,
            self.ngay_nghi,
        )

    def action_refuse(self):
        self.state = 'refuse'