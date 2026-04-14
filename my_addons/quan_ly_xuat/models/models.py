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
    ], string='Trạng thái', default='nhap')
    chi_tiet_xuat_ids = fields.One2many('quan_ly_xuat.chi_tiet_xuat', 'phieu_xuat_id', string='Chi tiết xuất')
    tong_so_luong = fields.Float(string='Tổng số lượng (kg)', compute='_compute_tong_so_luong', store=True)
    ly_do_xuat = fields.Text(string='Lý do xuất')

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


class ChiTietXuat(models.Model):
    _name = 'quan_ly_xuat.chi_tiet_xuat'
    _description = 'Chi tiết Phiếu Xuất Kho'

    phieu_xuat_id = fields.Many2one('quan_ly_xuat.phieu_xuat', string='Phiếu xuất', ondelete='cascade')
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string='Sản phẩm', required=True)
    so_luong = fields.Float(string='Số lượng (kg)', default=1.0, required=True)
    don_vi_tinh = fields.Char(string='Đơn vị tính', related='san_pham_id.don_vi_tinh', readonly=True)
    ghi_chu = fields.Char(string='Ghi chú')

