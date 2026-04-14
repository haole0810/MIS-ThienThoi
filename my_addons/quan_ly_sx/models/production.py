from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re
import unicodedata

class PhieuSanXuat(models.Model):
    _name = 'phieu.san.xuat'
    _description = 'Phiếu Sản Xuất Thiên Thời'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Mã Phiếu', required=True, default=lambda self: _('Mã tự động'), copy=False)
    ngay_tao = fields.Date(string='Ngày tạo', default=fields.Date.context_today, readonly=True)
    
    loai_phieu = fields.Selection([
        ('lua', 'Lựa bánh'),
        ('tron', 'Trộn bánh'),
        ('sot', 'Chế biến sốt bơ & sa tế')
    ], string='Bộ phận thực hiện', required=True)
    
    trang_thai = fields.Selection([
        ('cho', 'Chờ làm'),
        ('dang_lam', 'Đang thực hiện'),
        ('xong', 'Đã hoàn thành')
    ], default='cho', string='Trạng thái', tracking=True)

    product_id = fields.Many2one('thien_thoi_base.san_pham', string='Thành phẩm', required=True)
    so_luong = fields.Float(string='Số lượng dự kiến', default=1.0)
    so_luong_thanh_pham_dat = fields.Float(string='Thành phẩm đạt chuẩn')
    so_luong_nguyen_lieu_dung = fields.Float(string='Nguyên liệu thực tế đã dùng')
    hao_hut = fields.Float(string='Hao hụt (%)', compute='_compute_hao_hut', store=True)
    
    nguoi_lam_ids = fields.Many2many('res.users', string='Người phụ trách', default=lambda self: self.env.user)
    log_hoan_thanh = fields.Char(string='Nhóm thực hiện', readonly=True)

    def no_accent_vietnamese(self, s):
        """Hàm dọn dẹp dấu tiếng Việt"""
        if not s: return ""
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
        return s

    @api.depends('so_luong', 'so_luong_nguyen_lieu_dung', 'loai_phieu')
    def _compute_hao_hut(self):
        for record in self:
            if record.loai_phieu in ['lua', 'tron'] and record.so_luong > 0:
                record.hao_hut = ((record.so_luong_nguyen_lieu_dung - record.so_luong) / record.so_luong) * 100
            else:
                record.hao_hut = 0

    def action_start(self):
        for record in self:
            bom = self.env['thien.thoi.bom'].search([('product_id', '=', record.product_id.id)], limit=1)
            if not bom:
                raise UserError(f"Sản phẩm {record.product_id.display_name} chưa có BOM!")
            
            for line in bom.line_ids:
                needed_qty = line.quantity * record.so_luong
                inventory = self.env['thien_thoi_base.ton_kho'].search([('san_pham_id', '=', line.product_id.id)], limit=1)
                if not inventory or inventory.so_luong_hien_tai < needed_qty:
                    con_lai = inventory.so_luong_hien_tai if inventory else 0
                    raise UserError(f"Không đủ {line.product_id.display_name}! Cần {needed_qty} nhưng chỉ còn {con_lai}.")
            
            for user in record.nguoi_lam_ids:
                record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=user.id,
                    summary=f"Lệnh sản xuất mới: {record.name}",
                    note=f"Bạn có lệnh mới cho sản phẩm {record.product_id.display_name}. Mau làm đi nào!"
                )
            record.write({'trang_thai': 'dang_lam'})

    def action_done(self):
        for record in self:
            if record.trang_thai != 'dang_lam':
                raise UserError("Phiếu phải ở trạng thái 'Đang thực hiện' mới có thể hoàn thành.")
            if record.so_luong_thanh_pham_dat <= 0:
                raise UserError("Vui lòng nhập số lượng thành phẩm đạt chuẩn.")

            names = ", ".join(record.nguoi_lam_ids.mapped('name'))
            user = self.env.user
            log_msg = f"{user.name} đã xác nhận cho nhóm: {names}."

            bom = self.env['thien.thoi.bom'].search([('product_id', '=', record.product_id.id)], limit=1)
            if record.loai_phieu == 'sot':
                for line in bom.line_ids:
                    inv = self.env['thien_thoi_base.ton_kho'].search([('san_pham_id', '=', line.product_id.id)], limit=1)
                    if inv: inv.so_luong_hien_tai -= (line.quantity * record.so_luong)
            else:
                if bom.line_ids:
                    inv = self.env['thien_thoi_base.ton_kho'].search([('san_pham_id', '=', bom.line_ids[0].product_id.id)], limit=1)
                    if inv: inv.so_luong_hien_tai -= record.so_luong_nguyen_lieu_dung

            f_inv = self.env['thien_thoi_base.ton_kho'].search([('san_pham_id', '=', record.product_id.id)], limit=1)
            if f_inv: 
                f_inv.so_luong_hien_tai += record.so_luong_thanh_pham_dat
            else:
                self.env['thien_thoi_base.ton_kho'].create({
                    'ma_ton_kho': f'INV/{record.product_id.display_name}', 
                    'san_pham_id': record.product_id.id, 
                    'so_luong_hien_tai': record.so_luong_thanh_pham_dat, 
                    'kho_id': 1
                })

            record.activity_feedback(['mail.mail_activity_data_todo'])
            record.write({'trang_thai': 'xong', 'log_hoan_thanh': names})
            record.message_post(body=log_msg, message_type='comment', subtype_xmlid='mail.mt_note')

    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product = self.env['thien_thoi_base.san_pham'].browse(vals.get('product_id'))
            ten_sp = product.ten_sp if hasattr(product, 'ten_sp') else product.display_name
            
            # Chuyển tên thành KHÔNG DẤU và VIẾT HOA
            ten_sach = self.no_accent_vietnamese(ten_sp).upper()
            
            if ten_sach:
                words = ten_sach.split()
                if len(words) >= 2:
                    # Mã: Chữ đầu từ đầu + Chữ đầu từ cuối (ST, BB, NT...)
                    prefix = words[0][0] + words[-1][0]
                else:
                    # Mã: 2 chữ đầu của từ duy nhất (BO, SO, MU...)
                    prefix = words[0][:2]
            else:
                prefix = "SX"

            # Tìm số thứ tự lớn nhất cho Prefix này
            last_record = self.search([('name', 'like', prefix + '%')], order='name desc', limit=1)
            new_number = 1
            if last_record:
                last_numbers = re.findall(r'\d+', last_record.name)
                if last_numbers:
                    new_number = int(last_numbers[-1]) + 1
            
            vals['name'] = f"{prefix}{str(new_number).zfill(3)}"

        return super(PhieuSanXuat, self).create(vals)

# --- CẤU TRÚC ĐỊNH MỨC (BOM) ---

class ThienThoiBOM(models.Model):
    _name = 'thien.thoi.bom'
    _description = 'Công thức Thiên Thời'
    _rec_name = 'product_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one('thien_thoi_base.san_pham', string='Thành phẩm', required=True)
    line_ids = fields.One2many('thien.thoi.bom.line', 'bom_id', string='Nguyên liệu')
    quy_trinh = fields.Html(string='Quy trình hướng dẫn') 
    state = fields.Selection([('draft', 'Nháp'), ('validated', 'Đã xác nhận')], default='draft', string="Trạng thái")

    def action_validate(self):
        for record in self:
            # Chặn nếu không có nguyên liệu
            if not record.line_ids:
                raise UserError("Cần nhập nguyên liệu cho công thức trước khi xác nhận nhé!")
            
            # Chốt chặn định mức phải > 0
            if any(line.quantity <= 0 for line in record.line_ids):
                raise UserError("Định mức nguyên liệu cần phải lớn hơn 0 mới hợp lệ!")
        
        self.write({'state': 'validated'})
        self.message_post(body="Công thức đã được xác nhận.", subtype_xmlid='mail.mt_note')

    def action_set_to_draft(self):
        self.write({'state': 'draft'})

class ThienThoiBOMLine(models.Model):
    _name = 'thien.thoi.bom.line'
    _description = 'Chi tiết định mức'
    
    bom_id = fields.Many2one('thien.thoi.bom', ondelete='cascade')
    product_id = fields.Many2one('thien_thoi_base.san_pham', string='Nguyên liệu', required=True)
    
    # Thêm trường Loại nguyên liệu
    loai_nguyen_lieu = fields.Selection([
        ('chinh', 'Nguyên liệu chính'),
        ('gia_vi', 'Gia vị/Sốt'),
        ('bao_bi', 'Bao bì/Vật tư')
    ], string="Loại", default='chinh')

    quantity = fields.Float(string='Định mức', default=1.0, digits=(12, 3))

    # Thêm trường Đơn vị tính
    don_vi = fields.Selection([
        ('kg', 'Kilogam (kg)'),
        ('g', 'Gam (g)'),
        ('lit', 'Lít (l)'),
        ('cai', 'Cái/Xấp/Cuộn')
    ], string="Đơn vị", default='kg')