from odoo import models, fields, api
from odoo.exceptions import UserError

class PhieuNhapKho(models.Model):
    _name = 'quan_ly_nhap.phieu_nhap'
    _description = 'Phiếu Nhập Kho'
    _rec_name = 'ma_phieu'

    ma_phieu = fields.Char(
            string="Mã phiếu", 
            required=True, 
            copy=False, 
            readonly=True, 
            default='/'
        )
    ngay_nhap = fields.Date(string="Ngày nhập", default=fields.Date.context_today)
    tong_gia_tri = fields.Float(string="Tổng giá trị", compute='_compute_tong_tien', store=True)
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('da_xac_nhan', 'Đã xác nhận')
    ], string="Trạng thái", default='nhap')

    # --- LIÊN KẾT SANG MASTER DATA (thien_thoi_base) ---
    kho_id = fields.Many2one('thien_thoi_base.kho', string="Nhập vào Kho", required=True)
    nha_cung_cap_id = fields.Many2one('thien_thoi_base.nha_cung_cap', string="Nhà cung cấp", required=True)
    nguoi_dung_id = fields.Many2one('res.users', string="Người lập phiếu", default=lambda self: self.env.user)
    
    chi_tiet_nhap_ids = fields.One2many('quan_ly_nhap.chi_tiet_nhap', 'phieu_nhap_id', string="Chi tiết")

    @api.depends('chi_tiet_nhap_ids.so_luong_nhap', 'chi_tiet_nhap_ids.don_gia')
    def _compute_tong_tien(self):
        for phieu in self:
            phieu.tong_gia_tri = sum((line.so_luong_nhap * line.don_gia) for line in phieu.chi_tiet_nhap_ids)

    def xacNhan(self):
        for phieu in self:
            if phieu.trang_thai == 'da_xac_nhan':
                raise UserError("Phiếu này đã được xác nhận nhập kho trước đó!")
            if not phieu.chi_tiet_nhap_ids:
                raise UserError("Phải có ít nhất 1 sản phẩm để nhập kho!")

            for chi_tiet in phieu.chi_tiet_nhap_ids:
                # Tìm bản ghi tồn kho BÊN MODULE BASE
                ton_kho = self.env['thien_thoi_base.ton_kho'].search([
                    ('san_pham_id', '=', chi_tiet.san_pham_id.id),
                    ('kho_id', '=', phieu.kho_id.id)
                ], limit=1)

                if ton_kho:
                    ton_kho.so_luong_hien_tai += chi_tiet.so_luong_nhap
                    ton_kho.ngay_cap_nhat = fields.Date.context_today(self)
                else:
                    self.env['thien_thoi_base.ton_kho'].create({
                        'ma_ton_kho': f"TK-{chi_tiet.san_pham_id.id}-{phieu.kho_id.id}",
                        'san_pham_id': chi_tiet.san_pham_id.id,
                        'kho_id': phieu.kho_id.id,
                        'so_luong_hien_tai': chi_tiet.so_luong_nhap,
                    })

            phieu.trang_thai = 'da_xac_nhan'

    def write(self, vals):
        for phieu in self:
            if phieu.trang_thai == 'da_xac_nhan' and 'trang_thai' not in vals:
                raise UserError("Hệ thống Thiên Thời thông báo: Phiếu đã xác nhận không được phép sửa đổi!")
        return super(PhieuNhapKho, self).write(vals)

    def unlink(self):
        for phieu in self:
            if phieu.trang_thai == 'da_xac_nhan':
                raise UserError("Hệ thống Thiên Thời thông báo: Không thể xóa phiếu đã hoàn tất!")
        return super(PhieuNhapKho, self).unlink()
    def button_cancel(self):
        for phieu in self:
            if phieu.trang_thai != 'da_xac_nhan':
                continue
                
            for chi_tiet in phieu.chi_tiet_nhap_ids:
                # Tìm bản ghi tồn kho để trừ lại số lượng
                ton_kho = self.env['thien_thoi_base.ton_kho'].search([
                    ('san_pham_id', '=', chi_tiet.san_pham_id.id),
                    ('kho_id', '=', phieu.kho_id.id)
                ], limit=1)
                
                if ton_kho:
                    if ton_kho.so_luong_hien_tai < chi_tiet.so_luong_nhap:
                        raise UserError("Không thể hủy! Hàng trong kho đã được dùng hoặc xuất đi rồi.")
                    
                    ton_kho.so_luong_hien_tai -= chi_tiet.so_luong_nhap
            
            # Chuyển về trạng thái nháp để có thể sửa (write) hoặc xóa (unlink)
            phieu.trang_thai = 'nhap'
# Trường ảo để quét mã, không lưu vào DB (store=False)
    barcode_scan = fields.Char(string="Quét mã vạch sản phẩm", store=False)

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        if not self.barcode_scan:
            return

        # Tìm sản phẩm dựa trên ma_sp (được dùng làm barcode)
        product = self.env['thien_thoi_base.san_pham'].search([
            ('ma_sp', '=', self.barcode_scan)
        ], limit=1)

        if product:
            # Kiểm tra xem sản phẩm này đã có trong danh sách chi tiết chưa
            exists_line = self.chi_tiet_nhap_ids.filtered(lambda l: l.san_pham_id.id == product.id)
            
            if exists_line:
                # Nếu đã có, tự động tăng số lượng lên 1
                exists_line[0].so_luong_nhap += 1
            else:
                # Nếu chưa có, tạo dòng mới
                new_line = self.env['quan_ly_nhap.chi_tiet_nhap'].new({
                    'phieu_nhap_id': self._origin.id,
                    'san_pham_id': product.id,
                    'so_luong_nhap': 1.0,
                    'don_gia': 0.0, # Hoặc lấy gia_ban từ product làm mặc định
                })
                self.chi_tiet_nhap_ids += new_line
            
            # Xóa nội dung ô quét để chờ lần quét tiếp theo
            self.barcode_scan = False
        else:
            # Nếu không tìm thấy sản phẩm
            barcode_wrong = self.barcode_scan
            self.barcode_scan = False
            return {'warning': {
                'title': 'Không tìm thấy',
                'message': f'Sản phẩm có mã "{barcode_wrong}" không tồn tại trong hệ thống.'
            }}       
    def action_scan_barcode_mobile(self):
        """Mở camera quét barcode trên mobile - phiên bản đơn giản"""
        self.ensure_one()
        if self.trang_thai == 'da_xac_nhan':
            raise UserError("Phiếu đã xác nhận, không thể quét thêm!")

        return {
            'type': 'ir.actions.client',
            'tag': 'quan_ly_nhap_scan_barcode',   # tag mới, ngắn gọn
            'name': 'Quét Barcode',
            'params': {
                'phieu_id': self.id,
            },
        }

    @api.model
    def process_scanned_barcode(self, barcode, phieu_id):
        """Hàm xử lý trực tiếp việc thêm sản phẩm khi quét xong"""
        if not phieu_id:
            return {'error': 'Không tìm thấy ID phiếu nhập (ID trống)'}
        phieu = self.browse(int(phieu_id))
        if not phieu.exists() or phieu.trang_thai == 'da_xac_nhan':
            return {'error': 'Phiếu không hợp lệ hoặc đã xác nhận'}

        # Tìm sản phẩm dựa trên ma_sp
        product = self.env['thien_thoi_base.san_pham'].search([
            ('ma_sp', '=', barcode)
        ], limit=1)

        if not product:
            return {'error': f'Sản phẩm có mã "{barcode}" không tồn tại.'}

        # Kiểm tra xem sản phẩm đã có trong chi tiết chưa
        exists_line = phieu.chi_tiet_nhap_ids.filtered(lambda l: l.san_pham_id.id == product.id)
        
        if exists_line:
            # Nếu có rồi thì tăng số lượng
            exists_line[0].so_luong_nhap += 1
        else:
            # Nếu chưa có thì tạo mới (Dùng create thay vì new vì đây là gọi từ Backend)
            self.env['quan_ly_nhap.chi_tiet_nhap'].create({
                'phieu_nhap_id': phieu.id,
                'san_pham_id': product.id,
                'so_luong_nhap': 1.0,
                'don_gia': 0.0,
            })

        return {'success': True, 'message': f'Đã thêm sản phẩm {product.ten_sp}'}
    # Thêm hàm này vào class PhieuNhapKho của bạn
    @api.model
    def create(self, vals):
        # Nếu mã phiếu chưa có hoặc đang là mặc định, thì lấy số từ Sequence
        if vals.get('ma_phieu', '/') == '/':
            vals['ma_phieu'] = self.env['ir.sequence'].next_by_code('quan_ly_nhap.phieu_nhap') or '/'
        return super(PhieuNhapKho, self).create(vals)

    # Chỉnh lại trường ma_phieu một chút để nó mặc định là dấu /
class ChiTietNhap(models.Model):
    _name = 'quan_ly_nhap.chi_tiet_nhap'
    _description = 'Chi Tiết Phiếu Nhập'

    phieu_nhap_id = fields.Many2one('quan_ly_nhap.phieu_nhap', string="Phiếu nhập", ondelete='cascade')
    
    # --- LIÊN KẾT SANG MASTER DATA (thien_thoi_base) ---
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string="Sản phẩm", required=True,domain="[('loai_sp', 'in', ['gia_vi', 'banh_phoi', 'bao_bi'])]")
    
    so_luong_nhap = fields.Float(string="Số lượng nhập (kg)", required=True, default=1.0)
    don_gia = fields.Float(string="Đơn giá")
    chat_luong = fields.Selection([
        ('tot', 'Tốt'),
        ('loi', 'Lỗi')
    ], string="Chất lượng", default='tot')
    def action_open_label_wizard(self):
        self.ensure_one()
        return {
            'name': 'Cấu hình in tem sản phẩm',
            'type': 'ir.actions.act_window',
            'res_model': 'quan_ly_nhap.in_tem_wizard',
            'view_mode': 'form',
            'target': 'new', 
            'context': {
                'default_product_id': self.san_pham_id.id,
                'default_qty_total': self.so_luong_nhap,
                'default_so_luong_tem': 1, 
                'default_khoi_luong_moi_tem': self.so_luong_nhap,
            }
        }
class InTemWizard(models.TransientModel):
    _name = 'quan_ly_nhap.in_tem_wizard'
    _description = 'Wizard In Tem Dinh Danh'

    product_id = fields.Many2one('thien_thoi_base.san_pham', string="Sản phẩm", readonly=True)
    qty_total = fields.Float(string="Tổng khối lượng trên dòng", readonly=True)
    
    so_luong_tem = fields.Integer(string="Số lượng tem cần in", default=1, required=True)
    khoi_luong_moi_tem = fields.Float(string="Khối lượng mỗi tem (kg)", default=1.0, required=True)

    def action_confirm_print(self):
        """Hàm xử lý khi nhấn nút 'In Tem Ngay' trên Pop-up"""
        self.ensure_one()
        # Ở đây sau này mình sẽ viết lệnh xuất PDF hoặc đẩy ra máy in. 
        # Tạm thời trả về hiệu ứng cầu vồng cho vui mắt:
        return self.env.ref('quan_ly_nhap.action_report_in_tem_dinh_danh').report_action(self)