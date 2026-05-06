# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HopDongUploadWizard(models.TransientModel):
    _name = 'hop_dong.upload.wizard'
    _description = 'Wizard upload hợp đồng đã ký'

    hop_dong_id = fields.Many2one('nhan_su.hop_dong', string='Hợp đồng', required=True)
    file_upload = fields.Binary(string='Chọn file hợp đồng', required=True, attachment=True)
    file_name = fields.Char(string='Tên file', required=True)

    def action_confirm_upload(self):
        """Xác nhận upload file"""
        if not self.file_upload:
            raise UserError(_('Vui lòng chọn file để upload!'))

        self.hop_dong_id.write({
            'file_hop_dong_da_ky': self.file_upload,
            'file_hop_dong_name': self.file_name,
        })

        return {'type': 'ir.actions.act_window_close'}