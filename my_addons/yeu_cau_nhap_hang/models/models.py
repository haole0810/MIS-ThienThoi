from odoo import models, fields, api, _
from odoo.exceptions import UserError

class YeuCauNhapHang(models.Model):
    _name = 'yeu_cau_nhap_hang.request'
    _description = 'Yêu cầu nhập hàng tự động'
    _order = 'id desc'

    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string="Sản phẩm", readonly=True)
    kho_id = fields.Many2one('thien_thoi_base.kho', string="Kho thiếu hụt", readonly=True)
    so_luong_hien_tai = fields.Float(string="Tồn hiện tại", readonly=True)
    muc_toi_thieu = fields.Float(string="Mức tối thiểu", readonly=True)
    so_luong_can_nhap = fields.Float(string="Số lượng cần nhập", default=1.0)
    
    trang_thai = fields.Selection([
        ('cho_duyet', 'Chờ duyệt'),
        ('da_lap_phieu', 'Đã lập phiếu'),
        ('huy', 'Hủy bỏ')
    ], string="Trạng thái", default='cho_duyet', tracking=True)

    # Hàm quét tự động để tìm sản phẩm thiếu
    @api.model
    def cron_check_low_stock(self):
        # Tìm các bản ghi tồn kho bên module base có số lượng < mức tối thiểu
        low_stock_items = self.env['thien_thoi_base.ton_kho'].search([
            ('so_luong_hien_tai', '<', 'muc_toi_thieu')
        ])
        for item in low_stock_items:
            # Kiểm tra xem đã có yêu cầu Chờ duyệt nào cho sản phẩm này tại kho này chưa
            exists = self.search([
                ('san_pham_id', '=', item.san_pham_id.id),
                ('kho_id', '=', item.kho_id.id),
                ('trang_thai', '=', 'cho_duyet')
            ])
            if not exists:
                self.create({
                    'san_pham_id': item.san_pham_id.id,
                    'kho_id': item.kho_id.id,
                    'so_luong_hien_tai': item.so_luong_hien_tai,
                    'muc_toi_thieu': item.muc_toi_thieu,
                    'so_luong_can_nhap': item.muc_toi_thieu - item.so_luong_hien_tai
                })

    # Hàm xử lý khi Sếp bấm nút Duyệt
    def action_approve_and_import(self):
        if not self:
            return
        
        # Gom các yêu cầu cùng một kho để tạo một phiếu nhập
        # Ở đây mình giả định nhập từ Nhà cung cấp mặc định (id=1) 
        # Hào có thể chỉnh lại nha cung cấp theo thực tế
        phieu_nhap_vals = {
            'kho_id': self[0].kho_id.id,
            'nha_cung_cap_id': 1, 
            'chi_tiet_nhap_ids': []
        }

        for rec in self:
            if rec.trang_thai == 'cho_duyet':
                phieu_nhap_vals['chi_tiet_nhap_ids'].append((0, 0, {
                    'san_pham_id': rec.san_pham_id.id,
                    'so_luong_nhap': rec.so_luong_can_nhap,
                }))
                rec.trang_thai = 'da_lap_phieu'

        if phieu_nhap_vals['chi_tiet_nhap_ids']:
            new_phieu = self.env['quan_ly_nhap.phieu_nhap'].create(phieu_nhap_vals)
            return {
                'name': 'Phiếu Nhập Kho Vừa Tạo',
                'type': 'ir.actions.act_window',
                'res_model': 'quan_ly_nhap.phieu_nhap',
                'view_mode': 'form',
                'res_id': new_phieu.id,
                'target': 'current',
            }
class TonKhoInherit(models.Model):
    _inherit = 'thien_thoi_base.ton_kho'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(TonKhoInherit, self).create(vals_list)
        for record in records:
            record._check_and_create_import_request()
        return records

    def write(self, vals):
        res = super(TonKhoInherit, self).write(vals)
        # Nếu số lượng hiện tại bị thay đổi, thực hiện kiểm tra ngay
        if 'so_luong_hien_tai' in vals:
            for record in self:
                record._check_and_create_import_request()
        return res

    def _check_and_create_import_request(self):
        """Hàm kiểm tra logic và tạo yêu cầu nhập hàng ngay lập tức"""
        for record in self:
            if record.so_luong_hien_tai < record.muc_toi_thieu:
                # Kiểm tra xem đã có yêu cầu nháp chưa để tránh tạo trùng liên tục
                exists = self.env['yeu_cau_nhap_hang.request'].search([
                    ('san_pham_id', '=', record.san_pham_id.id),
                    ('kho_id', '=', record.kho_id.id),
                    ('trang_thai', '=', 'cho_duyet')
                ])
                if not exists:
                    self.env['yeu_cau_nhap_hang.request'].create({
                        'san_pham_id': record.san_pham_id.id,
                        'kho_id': record.kho_id.id,
                        'so_luong_hien_tai': record.so_luong_hien_tai,
                        'muc_toi_thieu': record.muc_toi_thieu,
                        'so_luong_can_nhap': record.muc_toi_thieu - record.so_luong_hien_tai
                    })