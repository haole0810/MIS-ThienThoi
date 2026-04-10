from odoo import models, fields

class Kho(models.Model):
    _name = 'thien_thoi_base.kho'
    _description = 'Quản lý danh mục Kho'
    _rec_name = 'ten_kho'

    ma_kho = fields.Char(string="Mã kho")
    ten_kho = fields.Char(string="Tên kho", required=True)
    dia_diem = fields.Char(string="Địa điểm")
    suc_chua = fields.Integer(string="Sức chứa (kg)")

class TonKho(models.Model):
    _name = 'thien_thoi_base.ton_kho'
    _description = 'Quản lý Tồn Kho'
    _rec_name = 'ma_ton_kho'

    ma_ton_kho = fields.Char(string="Mã tồn kho")
    so_luong_hien_tai = fields.Float(string="Số lượng hiện tại", default=0.0)
    muc_toi_thieu = fields.Float(string="Mức tối thiểu")
    ngay_cap_nhat = fields.Date(string="Ngày cập nhật", default=fields.Date.context_today)

    # Khóa ngoại nối với bảng Sản Phẩm và Kho trong cùng module này
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string="Sản phẩm", required=True)
    kho_id = fields.Many2one('thien_thoi_base.kho', string="Kho", required=True)

    def action_view_history(self):
        self.ensure_one()
        return {
            'name': 'Lịch sử nhập hàng: %s' % self.san_pham_id.ten_sp,
            'type': 'ir.actions.act_window',
            'res_model': 'quan_ly_nhap.chi_tiet_phieu_nhap',
            'view_mode': 'tree,form',
            'domain': [('san_pham_id', '=', self.san_pham_id.id)],
            'context': {'create': False},
        }