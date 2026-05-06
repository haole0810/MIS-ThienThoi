# -*- coding: utf-8 -*-
import base64
import os
import subprocess
import tempfile

from odoo import models, fields, api, _


class HopDongUploadWizard(models.TransientModel):
    _name = 'nhan_su.hop_dong.upload'
    _description = 'Upload Hợp đồng đã ký'

    hop_dong_id = fields.Many2one('nhan_su.hop_dong', string='Hợp đồng', required=False)
    nhan_vien_id = fields.Many2one('nhan_su.nhan_vien', string='Nhân viên')
    loai_hop_dong = fields.Selection([
        ('thu_viec', 'Thử việc (85%)'),
        ('chinh_thuc', 'Chính thức (100%)'),
    ], string='Loại hợp đồng', default='chinh_thuc')
    ngay_bat_dau = fields.Date(string='Ngày bắt đầu')
    ngay_ket_thuc = fields.Date(string='Ngày kết thúc')
    file_data = fields.Binary(string='Tải lên file', required=True)
    file_name = fields.Char(string='Tên file')
    state = fields.Selection([
        ('draft', 'Mới tạo'),
        ('active', 'Đang hiệu lực'),
        ('expiring', 'Sắp hết hạn'),
        ('expired', 'Hết hạn'),
        ('cancel', 'Đã hủy'),
    ], string='Trạng thái hợp đồng', default='active')

    @api.model
    def default_get(self, fields_list):
        res = super(HopDongUploadWizard, self).default_get(fields_list)
        contract_id = self.env.context.get('default_hop_dong_id') or self.env.context.get('active_id')
        if contract_id:
            contract = self.env['nhan_su.hop_dong'].browse(contract_id)
            res.update({
                'hop_dong_id': contract.id,
                'nhan_vien_id': contract.nhan_vien_id.id if contract.nhan_vien_id else False,
                'ngay_bat_dau': contract.ngay_bat_dau,
                'ngay_ket_thuc': contract.ngay_ket_thuc,
            })
        return res

    def _convert_to_pdf(self, file_bytes, file_name):
        """
        Convert file (DOCX/DOC/...) sang PDF dùng LibreOffice.
        Trả về bytes của PDF, hoặc None nếu thất bại.
        """
        ext = (file_name or '').lower().rsplit('.', 1)[-1]
        if ext == 'pdf':
            return file_bytes  # Đã là PDF, trả thẳng

        tmp_dir = tempfile.mkdtemp()
        try:
            # Ghi file gốc ra đĩa tạm
            src_path = os.path.join(tmp_dir, file_name or f'input.{ext}')
            with open(src_path, 'wb') as f:
                f.write(file_bytes)

            # Chạy LibreOffice headless convert
            result = subprocess.run(
                [
                    'soffice', '--headless', '--norestore',
                    '--convert-to', 'pdf',
                    '--outdir', tmp_dir,
                    src_path,
                ],
                capture_output=True,
                timeout=60,
            )

            # Tìm file PDF vừa tạo
            pdf_name = os.path.splitext(os.path.basename(src_path))[0] + '.pdf'
            pdf_path = os.path.join(tmp_dir, pdf_name)

            if result.returncode == 0 and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    return f.read()
            else:
                return None
        except Exception:
            return None
        finally:
            # Dọn dẹp file tạm
            for fname in os.listdir(tmp_dir):
                try:
                    os.remove(os.path.join(tmp_dir, fname))
                except Exception:
                    pass
            try:
                os.rmdir(tmp_dir)
            except Exception:
                pass

    def action_upload(self):
        """Lưu file vào hợp đồng, tự động convert sang PDF để xem trước"""
        self.ensure_one()

        if not self.file_data:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lỗi'),
                    'message': _('Vui lòng chọn file để tải lên'),
                    'type': 'danger',
                },
            }

        try:
            file_name = self.file_name or f'hop_dong_da_ky_{self.hop_dong_id.name}'
            file_bytes = base64.b64decode(self.file_data)

            # --- Convert sang PDF để xem trước ---
            pdf_bytes = self._convert_to_pdf(file_bytes, file_name)

            vals = {
                'nhan_vien_id': self.nhan_vien_id.id if self.nhan_vien_id else False,
                'ngay_bat_dau': self.ngay_bat_dau,
                'ngay_ket_thuc': self.ngay_ket_thuc,
            }

            if pdf_bytes:
                # Lưu bản PDF (để xem trước) vào trường chính
                pdf_name = os.path.splitext(file_name)[0] + '.pdf'
                preview_b64 = base64.b64encode(pdf_bytes)
                vals.update({
                    'file_hop_dong_da_ky': preview_b64,
                    'file_hop_dong_name': pdf_name,
                })
                msg = _('File hợp đồng đã được tải lên và chuyển đổi sang PDF thành công')
            else:
                # Convert thất bại → lưu file gốc
                vals.update({
                    'file_hop_dong_da_ky': self.file_data,
                    'file_hop_dong_name': file_name,
                })
                msg = _('File hợp đồng đã được tải lên (không thể chuyển đổi sang PDF để xem trước)')

            from odoo.exceptions import ValidationError
            if self.hop_dong_id:
                vals.update({
                    'state': 'active',
                })
                self.hop_dong_id.write(vals)
                target_contract = self.hop_dong_id
            else:
                if not self.nhan_vien_id:
                    raise ValidationError(_('Vui lòng chọn nhân viên khi tạo hợp đồng mới.'))
                vals.update({
                    'loai_hop_dong': self.loai_hop_dong,
                    'state': 'active',
                })
                target_contract = self.env['nhan_su.hop_dong'].create(vals)
                msg = _('Đã tạo mới hợp đồng lao động và tải lên file thành công.')

            # Tự động chuyển các hợp đồng cũ đang hiệu lực sang hết hạn
            if target_contract.nhan_vien_id:
                old_active_contracts = self.env['nhan_su.hop_dong'].search([
                    ('nhan_vien_id', '=', target_contract.nhan_vien_id.id),
                    ('id', '!=', target_contract.id),
                    ('state', '=', 'active'),
                ])
                if old_active_contracts:
                    old_active_contracts.write({'state': 'expired'})

            # Tạo attachment lưu file gốc
            self.env['ir.attachment'].create({
                'name': file_name,
                'datas': self.file_data,
                'res_model': 'nhan_su.hop_dong',
                'res_id': target_contract.id,
                'type': 'binary',
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': msg,
                    'type': 'success',
                },
            }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lỗi'),
                    'message': _('Lỗi khi tải lên file: %s') % str(e),
                    'type': 'danger',
                },
            }