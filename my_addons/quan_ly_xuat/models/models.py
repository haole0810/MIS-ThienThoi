# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class PhieuXuatKho(models.Model):
    _name = 'quan_ly_xuat.phieu_xuat'
    _description = 'Phiếu Xuất Kho'
    _rec_name = 'ma_phieu'

    ma_phieu = fields.Char(string='Mã phiếu', default='Mới', readonly=True)
    ngay_xuat = fields.Date(string='Ngày xuất', default=fields.Date.context_today)
    kho_id = fields.Many2one('thien_thoi_base.kho', string='Kho xuất', required=True)
    nguoi_xuat_id = fields.Many2one('res.users', string='Người xuất kho', default=lambda self: self.env.user)
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('xac_nhan', 'Đã xác nhận'),
        ('dong_goi', 'Đang đóng gói'),
        ('xuat_kho', 'Đã xuất kho'),
        ('huy', 'Đã hủy'),
    ], string='Trạng thái', default='nhap')
    chi_tiet_xuat_ids = fields.One2many('quan_ly_xuat.chi_tiet_xuat', 'phieu_xuat_id', string='Chi tiết xuất')
    tong_so_luong = fields.Float(string='Tổng số lượng (kg)', compute='_compute_tong_so_luong', store=True)
    thong_bao = fields.Text(string='Thông báo xuất kho', readonly=True)

    @api.depends('chi_tiet_xuat_ids.so_luong')
    def _compute_tong_so_luong(self):
        for record in self:
            record.tong_so_luong = sum(line.so_luong for line in record.chi_tiet_xuat_ids)

    def action_confirm(self):
        for record in self:
            if not record.chi_tiet_xuat_ids:
                raise UserError('Vui lòng thêm ít nhất một dòng sản phẩm trước khi xác nhận.')
            if record.ma_phieu == 'Mới':
                record.ma_phieu = self.env['ir.sequence'].next_by_code('quan_ly_xuat.phieu.xuat') or 'XK0001'
            record.trang_thai = 'xac_nhan'

    def action_pack(self):
        for record in self:
            if record.trang_thai != 'xac_nhan':
                raise UserError('Phiếu xuất kho phải ở trạng thái Đã xác nhận để đóng gói.')
            record.trang_thai = 'dong_goi'

    def action_done(self):
        for record in self:
            if record.trang_thai != 'dong_goi':
                raise UserError('Phiếu xuất kho phải ở trạng thái Đang đóng gói để xuất kho.')
            if not record.chi_tiet_xuat_ids:
                raise UserError('Phiếu xuất kho chưa có sản phẩm.')

            warning_lines = []
            for line in record.chi_tiet_xuat_ids:
                ton_kho = self.env['thien_thoi_base.ton_kho'].search([
                    ('san_pham_id', '=', line.san_pham_id.id),
                    ('kho_id', '=', record.kho_id.id)
                ], limit=1)
                if not ton_kho or ton_kho.so_luong_hien_tai < line.so_luong:
                    raise UserError(
                        f'Sản phẩm {line.san_pham_id.ten_sp} không đủ tồn kho để xuất. '
                        f'Hiện có {ton_kho.so_luong_hien_tai if ton_kho else 0.0} kg.'
                    )

                ton_kho.so_luong_hien_tai -= line.so_luong
                ton_kho.ngay_cap_nhat = fields.Date.context_today(self)

                if ton_kho.so_luong_hien_tai < ton_kho.muc_toi_thieu:
                    warning_lines.append(
                        f'{line.san_pham_id.ten_sp}: còn {ton_kho.so_luong_hien_tai} kg, '
                        f'dưới mức tối thiểu {ton_kho.muc_toi_thieu} kg.'
                    )
                    self.env['quan_ly_xuat.canh_bao_nhap'].create({
                        'phieu_xuat_id': record.id,
                        'ton_kho_id': ton_kho.id,
                        'so_luong_con_lai': ton_kho.so_luong_hien_tai,
                        'muc_toi_thieu': ton_kho.muc_toi_thieu,
                        'ghi_chu': 'Tồn kho đã xuống dưới mức cảnh báo sau khi xuất kho.',
                    })

            record.trang_thai = 'xuat_kho'
            record.thong_bao = '\n'.join(warning_lines) if warning_lines else 'Xuất kho thành công. Tồn kho đủ.'

    def action_cancel(self):
        for record in self:
            record.trang_thai = 'huy'


class ChiTietXuat(models.Model):
    _name = 'quan_ly_xuat.chi_tiet_xuat'
    _description = 'Chi tiết Phiếu Xuất Kho'

    phieu_xuat_id = fields.Many2one('quan_ly_xuat.phieu_xuat', string='Phiếu xuất', ondelete='cascade')
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string='Sản phẩm', required=True)
    so_luong = fields.Float(string='Số lượng (kg)', default=1.0, required=True)
    don_vi_tinh = fields.Char(string='Đơn vị tính', related='san_pham_id.don_vi_tinh', readonly=True)
    ghi_chu = fields.Char(string='Ghi chú')


class CanhBaoNhap(models.Model):
    _name = 'quan_ly_xuat.canh_bao_nhap'
    _description = 'Cảnh báo nhập hàng khi tồn kho thấp'

    phieu_xuat_id = fields.Many2one('quan_ly_xuat.phieu_xuat', string='Phiếu xuất kho', ondelete='set null')
    ton_kho_id = fields.Many2one('thien_thoi_base.ton_kho', string='Tồn kho', required=True)
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', related='ton_kho_id.san_pham_id', string='Sản phẩm', store=True, readonly=True)
    kho_id = fields.Many2one('thien_thoi_base.kho', related='ton_kho_id.kho_id', string='Kho', store=True, readonly=True)
    so_luong_con_lai = fields.Float(string='Số lượng còn lại', readonly=True)
    muc_toi_thieu = fields.Float(string='Mức tối thiểu', readonly=True)
    ghi_chu = fields.Text(string='Ghi chú')
    ngay_tao = fields.Date(string='Ngày tạo', default=fields.Date.context_today, readonly=True)
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('da_giai_quyet', 'Đã giải quyết'),
    ], string='Trạng thái', default='moi')

