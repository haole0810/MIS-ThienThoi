# -*- coding: utf-8 -*-
import pytz

from odoo import models, fields, api
from datetime import datetime, timedelta

class NhanVien(models.Model):
    _name = 'nhan_su.nhan_vien'
    _description = 'Thông tin nhân viên'
    ma_nv = fields.Char(string='Mã nhân viên', required=True, copy=False, default='Mới')
    name = fields.Char(string='Tên nhân viên', required=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Số điện thoại')
    chuc_vu_id = fields.Many2one('nhan_su.chuc_vu', string='Chức vụ')
    phong_ban_id = fields.Many2one('nhan_su.phong_ban', string='Phòng ban / Khu vực')
    
    # Thông tin cá nhân (phục vụ hợp đồng)
    ngay_sinh = fields.Date(string='Ngày sinh')
    so_cmnd = fields.Char(string='Số CMND/CCCD')
    ngay_cap_cmnd = fields.Date(string='Ngày cấp')
    noi_cap_cmnd = fields.Char(string='Nơi cấp')
    ho_khau_thuong_tru = fields.Char(string='Hộ khẩu thường trú')
    dia_chi_lien_he = fields.Char(string='Địa chỉ liên hệ')
    gioi_tinh = fields.Selection([('nam', 'Nam'), ('nu', 'Nữ'), ('khac', 'Khác')], string='Giới tính', default='nam')
    # Quan hệ
    ca_lam_id = fields.Many2one('nhan_su.ca_lam', string='Ca làm việc')
    cham_cong_ids = fields.One2many('nhan_su.cham_cong', 'nhan_vien_id', string='Dữ liệu chấm công')
    hop_dong_ids = fields.One2many('nhan_su.hop_dong', 'nhan_vien_id', string='Hợp đồng lao động')
    
    # Cài đặt lương
    luong_co_ban = fields.Float(string='Lương cơ bản', default=0.0)

    # Quy tắc tính lương
    he_so_ot = fields.Float(string='Hệ số OT', default=1.5, help='Hệ số tính tiền OT (ví dụ: 1.5 = 1.5 lần lương cơ bản)')
    so_gio_chuan_ngay = fields.Float(string='Số giờ chuẩn/ngày', default=8.0)
    so_ngay_cong_chuan_thang = fields.Float(string='Số ngày công chuẩn/tháng', default=26.0)
    mien_phat_di_tre_phut = fields.Float(string='Miễn phạt đi trễ (phút)', default=0.0, help='Dung sai đi trễ trước khi tính phạt')
    mien_phat_ve_som_phut = fields.Float(string='Miễn phạt về sớm (phút)', default=0.0, help='Dung sai về sớm trước khi tính phạt')
    
    # Mức phạt
    phat_di_tre_moi_phut = fields.Float(string='Phạt đi trễ/phút', default=0.0)
    phat_ve_som_moi_phut = fields.Float(string='Phạt về sớm/phút', default=0.0)

    @api.model
    def create(self, vals):
        if vals.get('ma_nv', 'Mới') == 'Mới':
            last_nv = self.search([], order='ma_nv desc', limit=1)
            if last_nv and last_nv.ma_nv.startswith('NV'):
                last_number = int(last_nv.ma_nv[2:])
                new_number = last_number + 1
                vals['ma_nv'] = f"NV{new_number:02d}"
            else:
                vals['ma_nv'] = "NV01"
        return super(NhanVien, self).create(vals)

class CaLam(models.Model):
    _name = 'nhan_su.ca_lam'
    _description = 'Cấu hình ca làm việc'

    name = fields.Char(string='Tên ca', required=True)
    gio_bat_dau = fields.Float(string='Giờ bắt đầu tổng (h)', required=True) # Ví dụ: 7.5
    gio_ket_thuc = fields.Float(string='Giờ kết thúc tổng (h)', required=True) # Ví dụ: 17.5
    
    # Chi tiết để in hợp đồng
    sang_tu = fields.Float(string='Sáng từ (h)', default=7.5)
    sang_den = fields.Float(string='Sáng đến (h)', default=11.5)
    chieu_tu = fields.Float(string='Chiều từ (h)', default=13.5)
    chieu_den = fields.Float(string='Chiều đến (h)', default=17.5)
    so_gio_ngay = fields.Float(string='Số giờ/ngày', default=8.0)
    so_ngay_tuan = fields.Integer(string='Số ngày/tuần', default=6)
    tu_thu = fields.Selection([('2', 'Thứ 2'), ('3', 'Thứ 3')], string='Từ thứ', default='2')
    den_thu = fields.Selection([('7', 'Thứ 7'), ('cn', 'Chủ nhật')], string='Đến thứ', default='7')

class ChamCong(models.Model):
    _name = 'nhan_su.cham_cong'
    _description = 'Dữ liệu chấm công'
    _order = 'ngay desc'

    nhan_vien_id = fields.Many2one('nhan_su.nhan_vien', string='Nhân viên', required=True)
    ngay = fields.Date(string='Ngày', default=fields.Date.context_today)
    gio_vao = fields.Datetime(string='Giờ vào')
    gio_ra = fields.Datetime(string='Giờ ra')
    # Các trường tính toán
    gio_lam = fields.Float(string='Giờ làm thực tế', compute='_compute_attendance_data', store=True)
    so_cong = fields.Float(string='Số công', compute='_compute_attendance_data', store=True)
    trang_thai = fields.Selection([
        ('binh_thuong', 'Bình thường'),
        ('di_tre', 'Đi trễ'),
        ('ve_som', 'Về sớm'),
        ('vi_pham', 'Trễ/Sớm')
    ], string='Trạng thái', compute='_compute_attendance_data', store=True)

    thoi_gian_tre = fields.Char(string='Đi trễ', compute='_compute_vi_pham_chi_tiet', store=True)
    thoi_gian_ve_som = fields.Char(string='Về sớm', compute='_compute_vi_pham_chi_tiet', store=True)
    
    @api.depends('gio_vao', 'gio_ra', 'nhan_vien_id.ca_lam_id')
    def _compute_attendance_data(self):
        # Lấy múi giờ hệ thống hoặc mặc định VN
        tz_name = self.env.context.get('tz') or 'Asia/Ho_Chi_Minh'
        user_tz = pytz.timezone(tz_name)

        for rec in self:
            rec.trang_thai = 'binh_thuong'
            rec.gio_lam = 0.0
            rec.so_cong = 0.0
            
            if not rec.gio_vao or not rec.nhan_vien_id.ca_lam_id:
                continue

            # 1. Chuyển đổi giờ vào/ra sang múi giờ VN để so sánh
            gio_vao_vn = pytz.utc.localize(rec.gio_vao).astimezone(user_tz)
            float_vao = gio_vao_vn.hour + gio_vao_vn.minute / 60.0
            
            ca = rec.nhan_vien_id.ca_lam_id
            
            # 2. Kiểm tra đi trễ
            is_late = float_vao > ca.gio_bat_dau
            
            # 3. Tính toán khi có giờ ra
            is_early = False
            if rec.gio_ra:
                gio_ra_vn = pytz.utc.localize(rec.gio_ra).astimezone(user_tz)
                float_ra = gio_ra_vn.hour + gio_ra_vn.minute / 60.0
                
                # Kiểm tra về sớm
                is_early = float_ra < ca.gio_ket_thuc
                
                # Tính tổng giờ làm
                diff = rec.gio_ra - rec.gio_vao
                duration = diff.total_seconds() / 3600.0
                rec.gio_lam = duration
                rec.so_cong = rec.gio_lam / 8.0

            # 4. Cập nhật trạng thái
            if is_late and is_early:
                rec.trang_thai = 'vi_pham'
            elif is_late:
                rec.trang_thai = 'di_tre'
            elif is_early:
                rec.trang_thai = 've_som'

    @api.depends('gio_vao', 'gio_ra', 'nhan_vien_id.ca_lam_id')
    def _compute_vi_pham_chi_tiet(self):
        for rec in self:
            # Gán giá trị mặc định
            rec.thoi_gian_tre = "Đúng giờ"
            rec.thoi_gian_ve_som = "Đúng giờ"
            
            ca = rec.nhan_vien_id.ca_lam_id
            if not ca:
                rec.thoi_gian_tre = rec.thoi_gian_ve_som = "Chưa gán ca"
                continue

            # --- 1. TÍNH TOÁN ĐI TRÊ ---
            if rec.gio_vao:
                # Chuyển giờ UTC sang giờ VN (UTC+7)
                gio_vao_vn = rec.gio_vao + timedelta(hours=7)
                # Đổi ra tổng số giây trong ngày
                giay_vao = (gio_vao_vn.hour * 3600) + (gio_vao_vn.minute * 60) + gio_vao_vn.second
                # Giờ bắt đầu ca (ví dụ 8.0 * 3600 = 28800 giây)
                giay_bat_dau = int((ca.gio_bat_dau or 0.0) * 3600)
                
                if giay_vao > giay_bat_dau:
                    diff = giay_vao - giay_bat_dau
                    h = diff // 3600
                    m = (diff % 3600) // 60
                    s = diff % 60
                    # Tạo chuỗi hiển thị
                    txt = []
                    if h > 0: txt.append(f"{int(h)}h")
                    if m > 0: txt.append(f"{int(m)}p")
                    txt.append(f"{int(s)}s")
                    rec.thoi_gian_tre = "Trễ " + " ".join(txt)

            # --- 2. TÍNH TOÁN VỀ SỚM ---
            if rec.gio_ra:
                # Chuyển giờ UTC sang giờ VN (UTC+7)
                gio_ra_vn = rec.gio_ra + timedelta(hours=7)
                # Đổi ra tổng số giây trong ngày
                giay_ra = (gio_ra_vn.hour * 3600) + (gio_ra_vn.minute * 60) + gio_ra_vn.second
                # Giờ kết thúc ca
                giay_ket_thuc = int((ca.gio_ket_thuc or 0.0) * 3600)
                
                if giay_ra < giay_ket_thuc:
                    diff = giay_ket_thuc - giay_ra
                    h = diff // 3600
                    m = (diff % 3600) // 60
                    s = diff % 60
                    # Tạo chuỗi hiển thị
                    txt = []
                    if h > 0: txt.append(f"{int(h)}h")
                    if m > 0: txt.append(f"{int(m)}p")
                    txt.append(f"{int(s)}s")
                    rec.thoi_gian_ve_som = "Sớm " + " ".join(txt)

    def _sync_payroll_for_attendance(self, previous_values=None):
        payroll_model = self.env['tinh_luong.bang_luong']
        for record in self:
            payroll_model._recompute_employee_payrolls(
                record.nhan_vien_id,
                record.ngay,
                record.ngay,
            )
            if previous_values and record.id in previous_values:
                old_employee, old_date = previous_values[record.id]
                if old_employee and old_date and (
                    old_employee.id != record.nhan_vien_id.id or old_date != record.ngay
                ):
                    payroll_model._recompute_employee_payrolls(old_employee, old_date, old_date)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_payroll_for_attendance()
        return records

    def write(self, vals):
        previous_values = {
            record.id: (record.nhan_vien_id, record.ngay)
            for record in self
        }
        result = super().write(vals)
        self._sync_payroll_for_attendance(previous_values)
        return result

    def unlink(self):
        previous_values = {
            record.id: (record.nhan_vien_id, record.ngay)
            for record in self
        }
        result = super().unlink()
        payroll_model = self.env['tinh_luong.bang_luong']
        for employee, date_value in previous_values.values():
            if employee and date_value:
                payroll_model._recompute_employee_payrolls(employee, date_value, date_value)
        return result

class PhongBan(models.Model):
    _name = 'nhan_su.phong_ban'
    _description = 'Phòng ban / Bộ phận'

    name = fields.Char(string='Tên phòng ban', required=True)
    ma_phong = fields.Char(string='Mã phòng')
    ghi_chu = fields.Text(string='Ghi chú khu vực')

class ChucVu(models.Model):
    _name = 'nhan_su.chuc_vu'
    _description = 'Chức vụ nhân sự'

    name = fields.Char(string='Tên chức vụ', required=True)
    ma_chuc_vu = fields.Char(string='Mã chức vụ')
    ghi_chu = fields.Text(string='Mô tả công việc')