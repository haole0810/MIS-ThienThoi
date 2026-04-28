from odoo import models, fields, api

class DonHangInherit(models.Model):
    _inherit = 'don_hang_banh_trang.don_hang'

    # Gom hết tất cả vào chung một hàm compute duy nhất
    voucher_id = fields.Many2one(
        'voucher.voucher', 
        string='Voucher áp dụng',
        compute='_compute_tong_hop',
        store=True 
    )
    tien_giam_gia = fields.Float(string='Tiền giảm giá', compute='_compute_tong_hop', store=True)
    tong_tien_sau_giam = fields.Float(string='Tổng thanh toán', compute='_compute_tong_hop', store=True)

    # Thêm 'loai_khach_hang' vào depends để đổi loại khách là nó tính lại liền
    @api.depends('chi_tiet_ids.so_luong', 'chi_tiet_ids.thanh_tien', 'loai_khach_hang')
    def _compute_tong_hop(self):
        # 1. Gọi hàm gốc để Odoo tính "tong_so_luong" và "tong_tien" trước
        super(DonHangInherit, self)._compute_tong_hop()
        
        # 2. Sau khi có số lượng và tổng tiền, mình nhảy vào tính Voucher luôn
        for rec in self:
            v_record = False
            
            # Kiểm tra: Chỉ khách sỉ và có mua hàng mới quét tìm voucher
            if rec.loai_khach_hang == 'si' and rec.tong_so_luong > 0:
                vouchers = self.env['voucher.voucher'].search([
                    ('trang_thai', '=', 'dang_chay'),
                    ('so_luong_toi_thieu', '<=', rec.tong_so_luong)
                ], order='so_luong_toi_thieu desc', limit=1)
                
                if vouchers:
                    v_record = vouchers[0]
            
            # Gắn mã voucher tìm được vào đơn hàng
            rec.voucher_id = v_record.id if v_record else False
            
            # Tính toán tiền giảm giá
            giam_gia = 0.0
            if v_record:
                if v_record.loai_giam_gia == 'tien_mat':
                    giam_gia = v_record.gia_tri_giam
                else: # Giảm theo phần trăm
                    giam_gia = (rec.tong_tien * v_record.gia_tri_giam) / 100.0
            
            # Chặn lỗi: Không cho phép tiền giảm lớn hơn tổng tiền đơn hàng
            if giam_gia > rec.tong_tien:
                giam_gia = rec.tong_tien
                
            rec.tien_giam_gia = giam_gia
            rec.tong_tien_sau_giam = rec.tong_tien - giam_gia