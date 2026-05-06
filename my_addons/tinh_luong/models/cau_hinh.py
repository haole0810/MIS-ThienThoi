# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class CauHinhTinhLuong(models.Model):
    _name = 'tinh_luong.cau_hinh'
    _description = 'Cấu hình tính lương'
    _singleton = True  # Chỉ có 1 bản ghi
    
    # Cấu hình công chuẩn
    tong_gio_lam_thang = fields.Float(string='Tổng giờ làm việc/tháng', default=208.0)
    so_ngay_cong_chuan_thang = fields.Float(string='Số công chuẩn/tháng', compute='_compute_so_ngay_cong_chuan_thang', store=True)
    so_gio_chuan_ngay = fields.Float(string='Số giờ chuẩn/ngày', default=8.0)

    @api.depends('tong_gio_lam_thang', 'so_gio_chuan_ngay')
    def _compute_so_ngay_cong_chuan_thang(self):
        for rec in self:
            if rec.so_gio_chuan_ngay:
                rec.so_ngay_cong_chuan_thang = rec.tong_gio_lam_thang / rec.so_gio_chuan_ngay
            else:
                rec.so_ngay_cong_chuan_thang = rec.tong_gio_lam_thang / 8.0
    
    # Đi trễ
    phat_di_tre_duoi_15 = fields.Float(string='Phạt đi trễ < 15 phút (VNĐ)', default=20000)
    phat_di_tre_15_30 = fields.Float(string='Phạt đi trễ 15 - 30 phút (VNĐ)', default=50000)
    phat_di_tre_30_60 = fields.Float(string='Phạt đi trễ 30 - 60 phút (VNĐ)', default=100000)

    # Về sớm
    phat_ve_som_duoi_15 = fields.Float(string='Phạt về sớm < 15 phút (VNĐ)', default=20000)
    phat_ve_som_15_30 = fields.Float(string='Phạt về sớm 15 - 30 phút (VNĐ)', default=50000)

    # Mức lương theo giờ
    muc_luong_nhan_vien = fields.Float(string='Mức lương nhân viên (VNĐ/giờ)', default=23000)
    muc_luong_quan_ly = fields.Float(string='Mức lương quản lý (VNĐ/giờ)', default=30000)

    # Hệ số tăng ca
    he_so_tang_ca_thuong = fields.Float(string='Hệ số tăng ca ngày thường', default=1.5)
    he_so_tang_ca_ngay_le = fields.Float(string='Hệ số tăng ca ngày lễ', default=3.0)

    # Demo tiền OT 1h
    demo_tien_ot_thuong = fields.Float(string='OT ngày thường/h (Nhân viên)', compute='_compute_demo_ot')
    demo_tien_ot_ngay_le = fields.Float(string='OT ngày lễ/h (Nhân viên)', compute='_compute_demo_ot')
    demo_tien_ot_thuong_ql = fields.Float(string='OT ngày thường/h (Quản lý)', compute='_compute_demo_ot')
    demo_tien_ot_ngay_le_ql = fields.Float(string='OT ngày lễ/h (Quản lý)', compute='_compute_demo_ot')

    @api.depends('muc_luong_nhan_vien', 'muc_luong_quan_ly', 'he_so_tang_ca_thuong', 'he_so_tang_ca_ngay_le')
    def _compute_demo_ot(self):
        for rec in self:
            rec.demo_tien_ot_thuong = (rec.muc_luong_nhan_vien or 0) * (rec.he_so_tang_ca_thuong or 0)
            rec.demo_tien_ot_ngay_le = (rec.muc_luong_nhan_vien or 0) * (rec.he_so_tang_ca_ngay_le or 0)
            rec.demo_tien_ot_thuong_ql = (rec.muc_luong_quan_ly or 0) * (rec.he_so_tang_ca_thuong or 0)
            rec.demo_tien_ot_ngay_le_ql = (rec.muc_luong_quan_ly or 0) * (rec.he_so_tang_ca_ngay_le or 0)

    def get_config(self):
        """Lấy cấu hình duy nhất"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({})
        return config
    
    def calculate_late_penalty(self, minutes, luong_ngay=0.0):
        """Tính phạt đi trễ"""
        if minutes <= 0:
            return 0.0
        elif minutes < 15:
            return self.phat_di_tre_duoi_15
        elif minutes <= 30:
            return self.phat_di_tre_15_30
        elif minutes <= 60:
            return self.phat_di_tre_30_60
        else:
            return luong_ngay / 2.0
    
    def calculate_early_penalty(self, minutes, luong_ngay=0.0):
        """Tính phạt về sớm"""
        if minutes <= 0:
            return 0.0
        elif minutes < 15:
            return self.phat_ve_som_duoi_15
        elif minutes <= 30:
            return self.phat_ve_som_15_30
        else:
            return luong_ngay / 2.0
