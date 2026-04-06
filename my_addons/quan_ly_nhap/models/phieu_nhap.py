from odoo import models, fields, api
from odoo.exceptions import UserError

class PhieuNhapKho(models.Model):
    _name = 'quan_ly_nhap.phieu_nhap'
    _description = 'Phiếu Nhập Kho'
    _rec_name = 'ma_phieu'

    ma_phieu = fields.Char(string="Mã phiếu", default="Mới")
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
            if phieu.trang_thai == 'da_xac_nhan':
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
    