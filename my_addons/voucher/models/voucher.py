# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Voucher(models.Model):
    _name = 'voucher.voucher'
    _description = 'Quản lý Voucher'
    _rec_name = 'ma_voucher'

    ma_voucher = fields.Char(string='Mã Voucher', required=True, copy=False)
    loai_giam_gia = fields.Selection([
        ('tien_mat', 'Giảm tiền mặt'),
        ('phan_tram', 'Giảm phần trăm (%)')
    ], string='Loại giảm giá', required=True, default='tien_mat')
    
    gia_tri_giam = fields.Float(string='Giá trị giảm', required=True)
    so_luong_toi_thieu = fields.Float(
        string='Số lượng tối thiểu (kg)', 
        required=True,
        default=0.0,
        help='Khách phải mua đạt tổng số lượng này mới được áp dụng voucher.'
    )
    ngay_bat_dau = fields.Date(string='Ngày bắt đầu', required=True, default=fields.Date.context_today)
    ngay_ket_thuc = fields.Date(string='Ngày kết thúc', required=True)
    
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('dang_chay', 'Đang áp dụng'),
        ('het_han', 'Hết hạn')
    ], string='Trạng thái', default='nhap')

    @api.constrains('gia_tri_giam', 'loai_giam_gia')
    def _check_gia_tri_giam(self):
        for rec in self:
            if rec.gia_tri_giam <= 0:
                raise ValidationError("Giá trị giảm phải lớn hơn 0.")
            if rec.loai_giam_gia == 'phan_tram' and rec.gia_tri_giam > 100:
                raise ValidationError("Giảm phần trăm không được vượt quá 100%.")

    def action_confirm(self):
        """Xác nhận voucher - chuyển từ trạng thái Nháp sang Đang áp dụng"""
        for rec in self:
            if rec.trang_thai != 'nhap':
                raise ValidationError("Chỉ có thể xác nhận voucher ở trạng thái Nháp!")
            
            # Kiểm tra các trường bắt buộc
            error_messages = []
            
            if not rec.ma_voucher or not rec.ma_voucher.strip():
                error_messages.append("• Mã Voucher không được để trống")
            
            if not rec.loai_giam_gia:
                error_messages.append("• Loại giảm giá phải được chọn")
            
            if rec.gia_tri_giam <= 0:
                error_messages.append("• Giá trị giảm phải lớn hơn 0")
            
            if rec.so_luong_toi_thieu <= 0:
                error_messages.append("• Số lượng tối thiểu phải lớn hơn 0")
            
            if not rec.ngay_bat_dau:
                error_messages.append("• Ngày bắt đầu không được để trống")
            
            if not rec.ngay_ket_thuc:
                error_messages.append("• Ngày kết thúc không được để trống")
            
            if rec.ngay_bat_dau and rec.ngay_ket_thuc and rec.ngay_bat_dau > rec.ngay_ket_thuc:
                error_messages.append("• Ngày bắt đầu phải nhỏ hơn ngày kết thúc")
            
            # Nếu có lỗi, throw ValidationError
            if error_messages:
                error_text = "❌ Không thể xác nhận voucher. Vui lòng kiểm tra:\n\n" + "\n".join(error_messages)
                raise ValidationError(error_text)
            
            # Nếu tất cả các trường hợp lệ, chuyển sang trạng thái Đang áp dụng
            rec.trang_thai = 'dang_chay'
        
        return True

    def write(self, values):
        """Ngăn chặn HOÀN TOÀN chỉnh sửa khi voucher đang áp dụng"""
        # Danh sách các field KHÔNG được sửa khi ở trạng thái "Đang áp dụng"
        protected_fields = {
            'ma_voucher', 'loai_giam_gia', 'gia_tri_giam', 
            'so_luong_toi_thieu', 'ngay_bat_dau', 'ngay_ket_thuc'
        }
        
        for rec in self:
            # Kiểm tra nếu record hiện tại đang ở trạng thái "Đang áp dụng"
            if rec.trang_thai == 'dang_chay':
                # Kiểm tra xem có field protected nào trong values không
                attempting_to_change = protected_fields & set(values.keys())
                
                if attempting_to_change:
                    field_names = ', '.join(sorted(attempting_to_change))
                    raise ValidationError(
                        f"⛔ KHÔNG ĐƯỢC PHÉP CHỈNH SỬA VOUCHER ĐANG ÁP DỤNG!\n\n"
                        f"Voucher '{rec.ma_voucher}' đang ở trạng thái 'Đang áp dụng' và bị LOCK.\n\n"
                        f"Các trường bị khóa: {field_names}\n\n"
                        f"Để chỉnh sửa, vui lòng:\n"
                        f"• Đổi trạng thái về 'Nháp' hoặc\n"
                        f"• Tạo voucher mới"
                    )
        
        return super().write(values)