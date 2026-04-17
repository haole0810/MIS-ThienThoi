# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class DonHang(models.Model):
    _name = 'don_hang_banh_trang.don_hang'
    _description = 'Đơn Hàng Bánh Tráng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_don_hang'
    _order = 'id desc'

    # ─── Thông tin chung ────────────────────────────────────────────────────────
    ma_don_hang = fields.Char(
        string='Mã đơn hàng',
        default='Mới',
        readonly=True,
        copy=False,
        tracking=True,
    )
    ngay_tao = fields.Date(
        string='Ngày tạo đơn',
        default=fields.Date.context_today,
        readonly=True,
        states={'xac_nhan': [('readonly', False)]},
        tracking=True,
    )
    ten_khach_hang = fields.Char(
        string='Tên khách hàng',
        required=True,
        tracking=True,
    )
    loai_khach_hang = fields.Selection([
        ('le', 'Khách lẻ'),
        ('si', 'Khách sỉ'),
    ], string='Loại khách hàng', required=True, default='le', tracking=True)

    # ─── Kho & Người thực hiện ──────────────────────────────────────────────────
    kho_id = fields.Many2one(
        'thien_thoi_base.kho',
        string='Kho xuất',
        required=True,
        tracking=True,
    )
    nguoi_xuat_id = fields.Many2one(
        'res.users',
        string='Người xuất kho',
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ─── Thông tin bổ sung ───────────────────────────────────────────────────────
    ly_do_xuat = fields.Text(
        string='Lý do xuất',
        default='Bán hàng',
    )
    ghi_chu = fields.Text(string='Ghi chú')

    # ─── Tổng hợp ────────────────────────────────────────────────────────────────
    tong_so_luong = fields.Float(
        string='Tổng số lượng (kg)',
        compute='_compute_tong_hop',
        store=True,
    )
    tong_tien = fields.Float(
        string='Tổng tiền (VNĐ)',
        compute='_compute_tong_hop',
        store=True,
    )

    # ─── Trạng thái ──────────────────────────────────────────────────────────────
    trang_thai = fields.Selection([
        ('xac_nhan', 'Xác nhận'),
        ('dong_goi', 'Đóng gói'),
        ('xuat_kho', 'Xuất kho'),
        ('huy', 'Hủy'),
    ], string='Trạng thái', default='xac_nhan', tracking=True, copy=False)

    # ─── Liên kết phiếu xuất ─────────────────────────────────────────────────────
    phieu_xuat_id = fields.Many2one(
        'quan_ly_xuat.phieu_xuat',
        string='Phiếu xuất kho',
        readonly=True,
        copy=False,
    )

    # ─── Chi tiết sản phẩm ───────────────────────────────────────────────────────
    chi_tiet_ids = fields.One2many(
        'don_hang_banh_trang.chi_tiet_don_hang',
        'don_hang_id',
        string='Chi tiết đơn hàng',
    )

    # ─── Computed ────────────────────────────────────────────────────────────────
    @api.depends('chi_tiet_ids.so_luong', 'chi_tiet_ids.thanh_tien')
    def _compute_tong_hop(self):
        for rec in self:
            rec.tong_so_luong = sum(line.so_luong for line in rec.chi_tiet_ids)
            rec.tong_tien = sum(line.thanh_tien for line in rec.chi_tiet_ids)

    # ─── Readonly helper ─────────────────────────────────────────────────────────
    @property
    def _is_locked(self):
        """Sau bước xác nhận, form bị khóa."""
        return self.trang_thai in ('dong_goi', 'xuat_kho', 'huy')

    # ─── Hành động ───────────────────────────────────────────────────────────────
    def action_dong_goi(self):
        """Chuyển sang bước Đóng gói. Khóa mọi thao tác chỉnh sửa."""
        for rec in self:
            if rec.trang_thai != 'xac_nhan':
                raise UserError('Chỉ có thể chuyển sang đóng gói từ trạng thái Xác nhận.')
            if not rec.chi_tiet_ids:
                raise UserError('Vui lòng thêm ít nhất một sản phẩm trước khi đóng gói.')

            # Sinh mã đơn hàng nếu chưa có
            if rec.ma_don_hang == 'Mới':
                rec.ma_don_hang = (
                    self.env['ir.sequence'].next_by_code('don_hang_banh_trang.don_hang')
                    or 'DH001'
                )
            rec.trang_thai = 'dong_goi'
            rec.message_post(body=f'Đơn hàng <b>{rec.ma_don_hang}</b> đã chuyển sang bước <b>Đóng gói</b>.')

    def action_xuat_kho(self):
        """
        Chuyển sang Xuất kho:
        1. Kiểm tra tồn kho từng sản phẩm.
        2. Trừ tồn kho.
        3. Tạo phiếu xuất kho tự động trong module quan_ly_xuat.
        """
        for rec in self:
            if rec.trang_thai != 'dong_goi':
                raise UserError('Chỉ có thể xuất kho từ trạng thái Đóng gói.')

            # Kiểm tra tồn kho
            for line in rec.chi_tiet_ids:
                ton_kho = self.env['thien_thoi_base.ton_kho'].search([
                    ('san_pham_id', '=', line.san_pham_id.id),
                    ('kho_id', '=', rec.kho_id.id),
                ], limit=1)
                so_luong_hien_co = ton_kho.so_luong_hien_tai if ton_kho else 0.0
                if so_luong_hien_co < line.so_luong:
                    raise UserError(
                        f'Sản phẩm "{line.san_pham_id.ten_sp}" không đủ tồn kho.\n'
                        f'Cần: {line.so_luong} kg  –  Hiện có: {so_luong_hien_co} kg.'
                    )

            # Trừ tồn kho & tạo phiếu xuất
            chi_tiet_xuat_vals = []
            for line in rec.chi_tiet_ids:
                ton_kho = self.env['thien_thoi_base.ton_kho'].search([
                    ('san_pham_id', '=', line.san_pham_id.id),
                    ('kho_id', '=', rec.kho_id.id),
                ], limit=1)
                ton_kho.so_luong_hien_tai -= line.so_luong
                ton_kho.ngay_cap_nhat = fields.Date.context_today(self)

                chi_tiet_xuat_vals.append((0, 0, {
                    'san_pham_id': line.san_pham_id.id,
                    'so_luong': line.so_luong,
                    'ghi_chu': f'Đơn hàng {rec.ma_don_hang} – {rec.ten_khach_hang}',
                }))

            # Tạo phiếu xuất kho trong quan_ly_xuat
            phieu_xuat = self.env['quan_ly_xuat.phieu_xuat'].create({
                'ngay_xuat': fields.Date.context_today(self),
                'kho_id': rec.kho_id.id,
                'nguoi_xuat_id': rec.nguoi_xuat_id.id,
                'ly_do_xuat': rec.ly_do_xuat or 'Bán hàng',
                'chi_tiet_xuat_ids': chi_tiet_xuat_vals,
                'trang_thai': 'xac_nhan',
            })
            # Sinh mã phiếu xuất nếu chưa có
            if phieu_xuat.ma_phieu == 'Mới':
                phieu_xuat.ma_phieu = (
                    self.env['ir.sequence'].next_by_code('quan_ly_xuat.phieu.xuat')
                    or 'XK0001'
                )

            rec.phieu_xuat_id = phieu_xuat.id
            rec.trang_thai = 'xuat_kho'
            rec.message_post(
                body=(
                    f'Đơn hàng <b>{rec.ma_don_hang}</b> đã <b>Xuất kho</b> thành công. '
                    f'Phiếu xuất: <b>{phieu_xuat.ma_phieu}</b>.'
                )
            )

    def action_huy(self):
        """Hủy đơn hàng – chỉ được hủy khi chưa xuất kho."""
        for rec in self:
            if rec.trang_thai == 'xuat_kho':
                raise UserError('Không thể hủy đơn hàng đã xuất kho.')
            rec.trang_thai = 'huy'
            rec.message_post(body=f'Đơn hàng <b>{rec.ma_don_hang}</b> đã bị <b>Hủy</b>.')

    def action_ve_xac_nhan(self):
        """Đưa đơn về lại Xác nhận (chỉ từ Đóng gói)."""
        for rec in self:
            if rec.trang_thai != 'dong_goi':
                raise UserError('Chỉ có thể đưa về Xác nhận từ trạng thái Đóng gói.')
            rec.trang_thai = 'xac_nhan'

    def action_xem_phieu_xuat(self):
        """Mở phiếu xuất kho liên quan."""
        self.ensure_one()
        if not self.phieu_xuat_id:
            raise UserError('Đơn hàng này chưa có phiếu xuất kho.')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'quan_ly_xuat.phieu_xuat',
            'view_mode': 'form',
            'res_id': self.phieu_xuat_id.id,
            'target': 'current',
        }


class ChiTietDonHang(models.Model):
    _name = 'don_hang_banh_trang.chi_tiet_don_hang'
    _description = 'Chi tiết Đơn Hàng Bánh Tráng'

    don_hang_id = fields.Many2one(
        'don_hang_banh_trang.don_hang',
        string='Đơn hàng',
        ondelete='cascade',
    )
    san_pham_id = fields.Many2one(
        'thien_thoi_base.san_pham',
        string='Sản phẩm',
        required=True,
    )
    don_vi_tinh = fields.Char(
        string='ĐVT',
        related='san_pham_id.don_vi_tinh',
        readonly=True,
    )
    so_luong = fields.Float(string='Số lượng (kg)', default=1.0, required=True)
    don_gia = fields.Float(string='Đơn giá (VNĐ)', required=True)
    thanh_tien = fields.Float(
        string='Thành tiền (VNĐ)',
        compute='_compute_thanh_tien',
        store=True,
    )
    ghi_chu = fields.Char(string='Ghi chú')
    @api.onchange('san_pham_id')
    def _onchange_san_pham_id(self):
        for line in self:
            if line.san_pham_id:
                # Dùng gia_ban vì module thien_thoi_base đặt tên như vậy
                line.don_gia = line.san_pham_id.gia_ban
    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for line in self:
            line.thanh_tien = line.so_luong * line.don_gia
