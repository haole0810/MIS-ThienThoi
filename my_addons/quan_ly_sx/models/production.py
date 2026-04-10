from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PhieuSanXuat(models.Model):
    _name = 'phieu.san.xuat'
    _description = 'Phiếu Sản Xuất Thiên Thời'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Mã Phiếu', required=True, default=lambda self: _('New'), copy=False)
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
    
    # 1. PHẦN KẾ HOẠCH
    so_luong = fields.Float(string='Số lượng dự kiến', default=1.0)
    
    # 2. PHẦN THỰC TẾ (Nhân viên nhập khi đang làm)
    so_luong_thanh_pham_dat = fields.Float(string='Thành phẩm đạt chuẩn')
    so_luong_nguyen_lieu_dung = fields.Float(string='Nguyên liệu thực tế đã dùng')
    
    # 3. TỰ ĐỘNG TÍNH TOÁN
    hao_hut = fields.Float(string='Hao hụt (%)', compute='_compute_hao_hut', store=True)
    nguoi_lam_id = fields.Many2one('res.users', string='Người phụ trách', default=lambda self: self.env.user)

    @api.depends('so_luong', 'so_luong_nguyen_lieu_dung', 'loai_phieu')
    def _compute_hao_hut(self):
        for record in self:
            # Đối với Lựa và Trộn: Hao hụt = (Thực dùng - Dự kiến) / Dự kiến
            if record.loai_phieu in ['lua', 'tron'] and record.so_luong > 0:
                record.hao_hut = ((record.so_luong_nguyen_lieu_dung - record.so_luong) / record.so_luong) * 100
            else:
                record.hao_hut = 0

# 1. Hàm Bắt đầu làm: KIỂM TRA TỒN KHO TRONG BẢNG TON_KHO
    def action_start(self):
        for record in self:
            bom = self.env['thien.thoi.bom'].search([('product_id', '=', record.product_id.id)], limit=1)
            if not bom:
                raise UserError(_("Sản phẩm %s chưa có BOM!") % record.product_id.display_name)
            
            for line in bom.line_ids:
                needed_qty = line.quantity * record.so_luong
                
                # TÌM TỒN KHO: Tìm trong bảng thien_thoi_base.ton_kho bản ghi khớp với sản phẩm này
                inventory = self.env['thien_thoi_base.ton_kho'].search([
                    ('san_pham_id', '=', line.product_id.id)
                ], limit=1)
                
                if not inventory or inventory.so_luong_hien_tai < needed_qty:
                    con_lai = inventory.so_luong_hien_tai if inventory else 0
                    raise UserError(_("Không đủ %s! Cần %.2f nma kho chỉ còn %.2f.") % 
                                    (line.product_id.display_name, needed_qty, con_lai))
            
            record.write({'trang_thai': 'dang_lam'})

    # 2. Hàm Hoàn thành: CẬP NHẬT TRỰC TIẾP VÀO BẢNG TON_KHO
    def action_done(self):
        for record in self:
            if record.trang_thai != 'dang_lam':
                raise UserError(_("Phiếu phải ở trạng thái 'Đang thực hiện'."))

            bom = self.env['thien.thoi.bom'].search([('product_id', '=', record.product_id.id)], limit=1)
            
            # --- BƯỚC 1: TRỪ KHO NGUYÊN LIỆU ---
            if record.loai_phieu == 'sot':
                for line in bom.line_ids:
                    qty_to_minus = line.quantity * record.so_luong
                    inventory = self.env['thien_thoi_base.ton_kho'].search([
                        ('san_pham_id', '=', line.product_id.id)
                    ], limit=1)
                    if inventory:
                        inventory.so_luong_hien_tai -= qty_to_minus
            else:
                if bom.line_ids:
                    main_material = bom.line_ids[0].product_id
                    inventory = self.env['thien_thoi_base.ton_kho'].search([
                        ('san_pham_id', '=', main_material.id)
                    ], limit=1)
                    if inventory:
                        inventory.so_luong_hien_tai -= record.so_luong_nguyen_lieu_dung

            # --- BƯỚC 2: CỘNG KHO THÀNH PHẨM ---
            finished_inv = self.env['thien_thoi_base.ton_kho'].search([
                ('san_pham_id', '=', record.product_id.id)
            ], limit=1)
            
            if finished_inv:
                finished_inv.so_luong_hien_tai += record.so_luong_thanh_pham_dat
            else:
                # Nếu thành phẩm chưa bao giờ có trong bảng tồn kho, tạo mới luôn
                self.env['thien_thoi_base.ton_kho'].create({
                    'ma_ton_kho': f'INV/{record.product_id.display_name}',
                    'san_pham_id': record.product_id.id,
                    'so_luong_hien_tai': record.so_luong_thanh_pham_dat,
                    'kho_id': 1 # Mặc định kho ID là 1, Việt kiểm tra ID kho thật trong DB nhé
                })

            record.write({'trang_thai': 'xong'})

    def action_admin_process(self):
        for record in self:
            # Sếp làm thay thì mặc định thực tế = kế hoạch
            if not record.so_luong_thanh_pham_dat:
                record.so_luong_thanh_pham_dat = record.so_luong
            if not record.so_luong_nguyen_lieu_dung:
                record.so_luong_nguyen_lieu_dung = record.so_luong
            record.action_start()
            record.action_done()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('phieu.san.xuat') or _('New')
        return super(PhieuSanXuat, self).create(vals)

# --- CẤU TRÚC ĐỊNH MỨC (BOM) & QUY TRÌNH ---

# --- CẤU TRÚC ĐỊNH MỨC (BOM) & QUY TRÌNH ĐÃ NÂNG CẤP ---

class ThienThoiBOM(models.Model):
    _name = 'thien.thoi.bom'
    _description = 'Công thức sản xuất Thiên Thời'
    _rec_name = 'product_id'
    # Thêm kế thừa để có khung thảo luận (Chatter) dưới chân trang
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one('thien_thoi_base.san_pham', string='Sản phẩm thành phẩm', required=True, tracking=True)
    line_ids = fields.One2many('thien.thoi.bom.line', 'bom_id', string='Nguyên liệu thành phần')
    quy_trinh = fields.Html(string='Quy trình hướng dẫn') 
    
    # Thêm trạng thái để kiểm soát công thức
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('validated', 'Đã xác nhận')
    ], string='Trạng thái', default='draft', tracking=True)

    # Nút bấm Xác nhận
    def action_validate(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_("Không thể xác nhận công thức rỗng! Vui lòng thêm nguyên liệu."))
            record.state = 'validated'
            # Ghi log vào khung chat khi xác nhận
            record.message_post(body=_("Công thức đã được xác nhận và khóa chỉnh sửa."))

    # Nút bấm Sửa lại (Chỉ dành cho người có quyền quản trị nếu muốn)
    def action_set_to_draft(self):
        for record in self:
            record.state = 'draft'
            record.message_post(body=_("Công thức đã được mở khóa để chỉnh sửa lại."))

class ThienThoiBOMLine(models.Model):
    _name = 'thien.thoi.bom.line'
    _description = 'Chi tiết nguyên liệu'

    bom_id = fields.Many2one('thien.thoi.bom', ondelete='cascade')
    product_id = fields.Many2one('thien_thoi_base.san_pham', string='Nguyên liệu', required=True)
    # Số lượng nguyên liệu cần để tạo ra 1 đơn vị thành phẩm
    quantity = fields.Float(string='Số lượng định mức', required=True, default=1.0)