# -*- coding: utf-8 -*-
import calendar
from datetime import timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')


class NhanVien(models.Model):
    _inherit = 'nhan_su.nhan_vien'

    luong_co_ban = fields.Float(string='Lương cơ bản')

    he_so_ot = fields.Float(string='Hệ số OT', default=1.5)
    so_gio_chuan_ngay = fields.Float(string='Số giờ chuẩn/ngày', default=8.0)
    so_ngay_cong_chuan_thang = fields.Float(string='Số công chuẩn/tháng', default=26.0)

    def action_preview_salary(self):
        """Tạo 1 bản xem trước tiền lương cho nhân viên (mặc định kỳ hiện tại)."""
        self.ensure_one()
        # Kỳ mặc định: tháng hiện tại
        from_date = fields.Date.context_today(self).replace(day=1)
        import calendar as _calendar
        last_day = _calendar.monthrange(from_date.year, from_date.month)[1]
        to_date = from_date.replace(day=last_day)

        # Kiểm tra dữ liệu
        self._validate_employee_data()

        Wizard = self.env['tinh_luong.preview']
        wiz = Wizard.create({
            'nhan_vien_id': self.id,
            'tu_ngay': from_date,
            'den_ngay': to_date,
        })
        wiz.compute_preview()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tinh_luong.preview',
            'res_id': wiz.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _validate_employee_data(self):
        """Kiểm tra xem nhân viên có đủ dữ liệu để tính lương không."""
        import logging
        _logger = logging.getLogger(__name__)
        
        checks = []
        checks.append(f"{'✓' if self.luong_co_ban else '✗'} Lương cơ bản: {self.luong_co_ban or 'KHÔNG CÓ'}")
        checks.append(f"{'✓' if self.ca_lam_id else '✗'} Ca làm: {self.ca_lam_id.name if self.ca_lam_id else 'KHÔNG CÓ'}")
        checks.append(f"{'✓' if self.cham_cong_ids else '✗'} Chấm công: {len(self.cham_cong_ids)} bản ghi")

        Config = self.env['tinh_luong.cau_hinh']
        config = Config.get_config()
        checks.append(f"  - Hệ số OT: {config.he_so_tang_ca_thuong or 1.5}")
        checks.append(f"  - Giờ chuẩn/ngày: {config.so_gio_chuan_ngay or 8}")
        checks.append(f"  - Công chuẩn/tháng: {config.so_ngay_cong_chuan_thang or 26}")
        
        info = f"\n[{self.name}] Kiểm tra dữ liệu:\n" + "\n".join(checks)
        _logger.info(info)



class TinhLuongBangLuong(models.Model):
    _name = 'tinh_luong.bang_luong'
    _description = 'Bảng lương'
    _order = 'tu_ngay desc, id desc'

    name = fields.Char(string='Mã bảng lương', required=True, copy=False, default='New')
    tu_ngay = fields.Date(string='Từ ngày', required=True, default=lambda self: self._default_from_date())
    den_ngay = fields.Date(string='Đến ngày', required=True, default=lambda self: self._default_to_date())
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('computed', 'Đã tính'),
        ('done', 'Đã chốt'),
    ], string='Trạng thái', default='draft', required=True)
    line_ids = fields.One2many('tinh_luong.bang_luong.line', 'bang_luong_id', string='Chi tiết lương')
    so_nhan_vien = fields.Integer(string='Số nhân viên', compute='_compute_totals', store=True)
    tong_gio_cong = fields.Float(string='Tổng giờ công', compute='_compute_totals', store=True)
    tong_gio_ot = fields.Float(string='Tổng giờ OT', compute='_compute_totals', store=True)
    tong_phat = fields.Monetary(string='Tổng phạt', compute='_compute_totals', store=True, currency_field='currency_id')
    tong_luong = fields.Monetary(string='Tổng lương', compute='_compute_totals', store=True, currency_field='currency_id')
    tong_thuc_nhan = fields.Monetary(string='Tổng thực nhận', compute='_compute_totals', store=True, currency_field='currency_id')

    @api.model
    def _default_from_date(self):
        today = fields.Date.context_today(self)
        return today.replace(day=1)

    @api.model
    def _default_to_date(self):
        today = fields.Date.context_today(self)
        last_day = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=last_day)

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tinh_luong.bang_luong') or 'New'
        return super().create(vals)

    def _recompute_employee_payrolls(self, employee, from_date, to_date):
        if not employee or not from_date or not to_date:
            return

        if isinstance(from_date, str):
            from_date = fields.Date.to_date(from_date)
        if isinstance(to_date, str):
            to_date = fields.Date.to_date(to_date)

        payrolls = self.search([
            ('tu_ngay', '<=', to_date),
            ('den_ngay', '>=', from_date),
            ('state', '!=', 'done'),
        ])
        Line = self.env['tinh_luong.bang_luong.line']
        for payroll in payrolls:
            line = payroll.line_ids.filtered(lambda rec: rec.nhan_vien_id.id == employee.id)[:1]
            if not line and payroll.state in ('draft', 'computed'):
                line = Line.create({
                    'bang_luong_id': payroll.id,
                    'nhan_vien_id': employee.id,
                })
            if line:
                line._compute_salary_line()

    @api.constrains('tu_ngay', 'den_ngay')
    def _check_date_range(self):
        for record in self:
            if record.tu_ngay and record.den_ngay and record.tu_ngay > record.den_ngay:
                raise ValidationError('Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc.')

    def action_compute_salary(self):
        import logging
        _logger = logging.getLogger(__name__)
        
        HopDong = self.env['nhan_su.hop_dong']
        
        for record in self:
            employees = self.env['nhan_su.nhan_vien'].search([])
            commands = []
            
            # Kiểm tra từng nhân viên
            warnings = []
            for employee in employees:
                # 1. Kiểm tra hợp đồng
                contract = HopDong.search([
                    ('nhan_vien_id', '=', employee.id),
                    ('ngay_bat_dau', '<=', record.tu_ngay),
                    ('state', '=', 'active'),
                    '|',
                    ('ngay_ket_thuc', '=', False),
                    ('ngay_ket_thuc', '>=', record.tu_ngay),
                ], limit=1)
                
                if not contract:
                    warnings.append(f"⚠️ {employee.name}: Không có hợp đồng hoạt động trong kỳ này")
                
                # 2. Kiểm tra ca làm việc
                if not employee.ca_lam_id:
                    warnings.append(f"⚠️ {employee.name}: Chưa gán ca làm việc")
                
                # 3. Kiểm tra chấm công
                attendances = employee.cham_cong_ids.filtered(
                    lambda att: att.ngay and record.tu_ngay <= att.ngay <= record.den_ngay
                )
                if not attendances:
                    warnings.append(f"ℹ️ {employee.name}: Không có chấm công trong kỳ này")
                
                commands.append((0, 0, {
                    'nhan_vien_id': employee.id,
                }))
            
            # Log warnings
            if warnings:
                warning_msg = "\n".join(warnings[:10])  # Show 10 cái đầu
                _logger.warning(f"Tính lương - Cảnh báo dữ liệu:\n{warning_msg}")
            
            record.line_ids = [(5, 0, 0)] + commands
            for line in record.line_ids:
                line._compute_salary_line()
            record.state = 'computed'
        return True

    def action_set_draft(self):
        self.state = 'draft'

    def action_done(self):
        self.state = 'done'

    def action_send_payslips(self):
        """Gửi email bảng lương tới từng nhân viên (dựa trên mỗi line)."""
        self.ensure_one()
        template = self.env.ref('tinh_luong.email_template_payslip', False)
        if not template:
            raise UserError('Không tìm thấy email template phần mềm. Vui lòng cài đặt template.')
        missing = []
        sent = 0
        for line in self.line_ids:
            email = line.nhan_vien_id.email
            if not email:
                missing.append(line.nhan_vien_id.name or line.nhan_vien_id.ma_nv)
                continue
            try:
                template.send_mail(line.id, force_send=False)
                sent += 1
            except Exception as e:
                # log and continue
                _logger = getattr(self, '_logger', None)
                if _logger:
                    _logger.error('Failed to send payslip to %s: %s', email, e)
        if missing:
            raise UserError('Một số nhân viên không có email: %s' % (', '.join(missing)))
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': f'Đã tạo và đưa {sent} thư vào hàng đợi (Outbox). Vui lòng kiểm tra trong Cấu hình -> Kỹ thuật -> Email.',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.depends('line_ids.tong_luong', 'line_ids.tien_phat_di_tre', 'line_ids.tien_phat_ve_som',
                 'line_ids.gio_cong_thuc_te', 'line_ids.gio_ot')
    def _compute_totals(self):
        for record in self:
            record.so_nhan_vien = len(record.line_ids)
            record.tong_gio_cong = sum(record.line_ids.mapped('gio_cong_thuc_te'))
            record.tong_gio_ot = sum(record.line_ids.mapped('gio_ot'))
            record.tong_phat = sum(record.line_ids.mapped('tien_phat_di_tre')) + sum(record.line_ids.mapped('tien_phat_ve_som'))
            record.tong_luong = sum(record.line_ids.mapped('tong_luong'))
            record.tong_thuc_nhan = sum(record.line_ids.mapped('thuc_nhan'))


class TinhLuongBangLuongLine(models.Model):
    _name = 'tinh_luong.bang_luong.line'
    _description = 'Chi tiết bảng lương'
    _order = 'nhan_vien_id'

    bang_luong_id = fields.Many2one('tinh_luong.bang_luong', string='Bảng lương', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='bang_luong_id.currency_id', store=True, readonly=True)
    nhan_vien_id = fields.Many2one('nhan_su.nhan_vien', string='Nhân viên', required=True)
    ma_nv = fields.Char(string='Mã NV', related='nhan_vien_id.ma_nv', store=True, readonly=True)
    chuc_vu_id = fields.Many2one(related='nhan_vien_id.chuc_vu_id', store=True, readonly=True)
    phong_ban_id = fields.Many2one(related='nhan_vien_id.phong_ban_id', store=True, readonly=True)
    luong_co_ban = fields.Float(string='Lương cơ bản')

    he_so_ot = fields.Float(string='Hệ số OT', default=1.5)
    so_gio_chuan_ngay = fields.Float(string='Số giờ chuẩn/ngày', default=8.0)
    so_ngay_cong_chuan_thang = fields.Float(string='Số công chuẩn/tháng', default=26.0)
    so_cong_thuc_te = fields.Float(string='Số công thực tế')
    gio_cong_thuc_te = fields.Float(string='Giờ công thực tế')
    gio_nghi_phep_co_luong = fields.Float(string='Giờ nghỉ phép có lương')
    gio_nghi_khong_luong = fields.Float(string='Giờ nghỉ không lương')
    gio_ot = fields.Float(string='Giờ OT')
    so_lan_di_tre = fields.Integer(string='Số lần đi trễ')
    so_lan_ve_som = fields.Integer(string='Số lần về sớm')
    phut_di_tre = fields.Integer(string='Tổng phút đi trễ')
    phut_ve_som = fields.Integer(string='Tổng phút về sớm')
    luong_gio = fields.Monetary(string='Lương giờ', currency_field='currency_id')
    luong_ngay = fields.Monetary(string='Lương ngày', currency_field='currency_id')
    luong_cong_thuc_te = fields.Monetary(string='Lương công thực tế', currency_field='currency_id')

    tien_ot = fields.Monetary(string='Tiền OT', currency_field='currency_id')
    tien_phat_di_tre = fields.Monetary(string='Phạt đi trễ', currency_field='currency_id')
    tien_phat_ve_som = fields.Monetary(string='Phạt về sớm', currency_field='currency_id')
    tong_phat = fields.Monetary(string='Tổng phạt', currency_field='currency_id')
    tong_luong = fields.Monetary(string='Tổng lương', currency_field='currency_id')
    thuc_nhan = fields.Monetary(string='Thực nhận', currency_field='currency_id')
    ghi_chu = fields.Char(string='Ghi chú')

    def _to_vn_datetime(self, dt_value):
        if not dt_value:
            return False
        if dt_value.tzinfo:
            utc_dt = dt_value.astimezone(pytz.UTC)
        else:
            utc_dt = pytz.utc.localize(dt_value)
        return utc_dt.astimezone(VN_TZ)

    def _get_shift_hours(self, employee):
        shift = employee.ca_lam_id
        if not shift:
            return 0.0
        start = shift.gio_bat_dau or 0.0
        end = shift.gio_ket_thuc or 0.0
        if end >= start:
            return end - start
        return (24.0 - start) + end

    def _get_local_hour(self, dt_value):
        local_dt = self._to_vn_datetime(dt_value)
        if not local_dt:
            return 0.0
        return local_dt.hour + (local_dt.minute / 60.0) + (local_dt.second / 3600.0)

    def _get_attendance_hours(self, attendance):
        if attendance.gio_vao and attendance.gio_ra:
            return max((attendance.gio_ra - attendance.gio_vao).total_seconds() / 3600.0, 0.0)
        return attendance.gio_lam or 0.0

    def _compute_salary_line(self):
        import logging
        _logger = logging.getLogger(__name__)
        
        for line in self:
            employee = line.nhan_vien_id
            payroll = line.bang_luong_id
            
            # Kiểm tra ngày: nếu không có ngày bắt đầu/kết thúc thì reset toàn bộ
            if not payroll or not payroll.tu_ngay or not payroll.den_ngay:
                line.so_cong_thuc_te = 0.0
                line.gio_cong_thuc_te = 0.0
                line.gio_nghi_phep_co_luong = 0.0
                line.gio_nghi_khong_luong = 0.0
                line.gio_ot = 0.0
                line.so_lan_di_tre = 0
                line.so_lan_ve_som = 0
                line.phut_di_tre = 0
                line.phut_ve_som = 0
                line.luong_gio = 0.0
                line.luong_ngay = 0.0
                line.luong_cong_thuc_te = 0.0
                line.tien_ot = 0.0
                line.tien_phat_di_tre = 0.0
                line.tien_phat_ve_som = 0.0
                line.tong_phat = 0.0
                line.tong_luong = 0.0
                line.ghi_chu = 'Thiếu ngày kỳ tính lương'
                continue

            # 1. LẤY HỢP ĐỒNG HOẠT ĐỘNG của nhân viên
            HopDong = self.env['nhan_su.hop_dong']
            contract = HopDong.search([
                ('nhan_vien_id', '=', employee.id),
                ('ngay_bat_dau', '<=', payroll.tu_ngay),
                ('state', '=', 'active'),
                '|',
                ('ngay_ket_thuc', '=', False),
                ('ngay_ket_thuc', '>=', payroll.tu_ngay),
            ], limit=1)
            
            # 2. LẤY CẤU HÌNH TÍNH LƯƠNG
            Config = self.env['tinh_luong.cau_hinh']
            config = Config.get_config()
            
            # 3. GÁN DỮ LIỆU TỪ HỢP ĐỒNG HOẶC NHÂN VIÊN DIRECTLY
            if contract:
                line.luong_co_ban = contract.luong_co_ban
            else:
                line.luong_co_ban = employee.luong_co_ban
            
            # 4. SỬ DỤNG CẤU HÌNH
            line.so_gio_chuan_ngay = config.so_gio_chuan_ngay
            line.so_ngay_cong_chuan_thang = config.so_ngay_cong_chuan_thang
            line.he_so_ot = config.he_so_tang_ca_thuong
            
            # 5. LẤY DỮ LIỆU CHẤM CÔNG
            _logger.info(f'[{employee.name}] Tìm chấm công từ {payroll.tu_ngay} đến {payroll.den_ngay}')
            attendances = employee.cham_cong_ids.filtered(
                lambda att: att.ngay and payroll.tu_ngay <= att.ngay <= payroll.den_ngay
            )
            _logger.info(f'[{employee.name}] Tìm được {len(attendances)} bản chấm công')
            
            # 6. LẤY DỮ LIỆU NGHỈ PHÉP
            leaves = self.env['nhan_su.nghi_phep'].search([
                ('nhan_vien_id', '=', employee.id),
                ('ngay_nghi', '>=', payroll.tu_ngay),
                ('ngay_nghi', '<=', payroll.den_ngay),
                ('state', '=', 'validate'),
            ])

            shift_hours = line._get_shift_hours(employee)
            standard_hours = line.so_gio_chuan_ngay or 8.0
            month_hours = (line.so_ngay_cong_chuan_thang or 1.0) * standard_hours
            line.luong_gio = (line.luong_co_ban / month_hours) if month_hours else 0.0
            line.luong_ngay = (line.luong_co_ban / line.so_ngay_cong_chuan_thang) if line.so_ngay_cong_chuan_thang else 0.0

            regular_hours = 0.0
            overtime_hours = 0.0
            late_minutes = 0
            early_minutes = 0
            late_count = 0
            early_count = 0

            # DEBUG: Log thông tin nhân viên
            _logger.info(f'[{employee.name}] Shift hours: {shift_hours}, Standard: {standard_hours}')
            _logger.info(f'[{employee.name}] Ca làm: {employee.ca_lam_id.name if employee.ca_lam_id else "Không gán"}')

            for attendance in attendances:
                actual_hours = line._get_attendance_hours(attendance)
                regular_hours += min(actual_hours, shift_hours or actual_hours)
                overtime_hours += max(actual_hours - (shift_hours or actual_hours), 0.0)
                
                _logger.info(f'[{employee.name}] Ngày {attendance.ngay}: {actual_hours}h làm, status={attendance.trang_thai}')

                if employee.ca_lam_id and attendance.gio_vao:
                    late = max(line._get_local_hour(attendance.gio_vao) - (employee.ca_lam_id.gio_bat_dau or 0.0), 0.0)
                    late_min = int(round(late * 60))
                    if late_min > (employee.mien_phat_di_tre_phut or 0.0):
                        late_count += 1
                        late_minutes += late_min

                if employee.ca_lam_id and attendance.gio_ra:
                    early = max((employee.ca_lam_id.gio_ket_thuc or 0.0) - line._get_local_hour(attendance.gio_ra), 0.0)
                    early_min = int(round(early * 60))
                    if early_min > (employee.mien_phat_ve_som_phut or 0.0):
                        early_count += 1
                        early_minutes += early_min

            paid_leave_days = len(leaves.filtered(lambda leave: leave.loai_nghi == 'phep'))
            unpaid_leave_days = len(leaves.filtered(lambda leave: leave.loai_nghi == 'khong_phep'))
            
            _logger.info(f'[{employee.name}] Tổng: {regular_hours}h thường, {overtime_hours}h OT, {paid_leave_days} ngày phép, trễ {late_minutes}p, sớm {early_minutes}p')

            line.so_cong_thuc_te = regular_hours / standard_hours if standard_hours else 0.0
            line.gio_cong_thuc_te = abs(regular_hours)
            line.gio_nghi_phep_co_luong = paid_leave_days * standard_hours
            line.gio_nghi_khong_luong = unpaid_leave_days * standard_hours
            line.gio_ot = overtime_hours
            line.so_lan_di_tre = late_count
            line.so_lan_ve_som = early_count
            line.phut_di_tre = late_minutes
            line.phut_ve_som = early_minutes

            # TÍNH PHẠT SỬ DỤNG CẤU HÌNH
            line.tien_phat_di_tre = config.calculate_late_penalty(late_minutes, line.luong_ngay)
            line.tien_phat_ve_som = config.calculate_early_penalty(early_minutes, line.luong_ngay)
            line.tong_phat = line.tien_phat_di_tre + line.tien_phat_ve_som

            line.luong_cong_thuc_te = (regular_hours + line.gio_nghi_phep_co_luong) * line.luong_gio
            line.tien_ot = overtime_hours * line.luong_gio * (line.he_so_ot or 1.0)
            line.tong_luong = (
                line.luong_cong_thuc_te
                + line.tien_ot
            )
            line.thuc_nhan = line.tong_luong - line.tong_phat
            
            # Thêm thông tin debug vào ghi chú
            notes = [f'✓ {len(attendances)} ngày công']
            if paid_leave_days > 0:
                notes.append(f'✓ {paid_leave_days} ngày phép')
            if unpaid_leave_days > 0:
                notes.append(f'ℹ️ {unpaid_leave_days} ngày không phép')
            if overtime_hours > 0:
                notes.append(f'✓ {overtime_hours:.1f}h OT')
            if late_count > 0:
                notes.append(f'⚠️ Trễ {late_count}x ({late_minutes}p)')
            if early_count > 0:
                notes.append(f'⚠️ Sớm {early_count}x ({early_minutes}p)')
            
            line.ghi_chu = ' | '.join(notes) if notes else 'Không có dữ liệu công việc'
            
            _logger.info(f'[{employee.name}] Kết quả lương: {line.tong_luong}')


class TinhLuongPreview(models.TransientModel):
    _name = 'tinh_luong.preview'
    _description = 'Xem trước lương'

    nhan_vien_id = fields.Many2one('nhan_su.nhan_vien', string='Nhân viên', required=True)
    tu_ngay = fields.Date(string='Từ ngày', required=True)
    den_ngay = fields.Date(string='Đến ngày', required=True)

    # Fields to show
    luong_co_ban = fields.Float(string='Lương cơ bản')
    luong_gio = fields.Float(string='Lương giờ')
    gio_cong_thuc_te = fields.Float(string='Giờ công thực tế')
    gio_nghi_phep_co_luong = fields.Float(string='Giờ nghỉ phép có lương')
    gio_nghi_khong_luong = fields.Float(string='Giờ nghỉ không lương')
    gio_ot = fields.Float(string='Giờ OT')

    tien_ot = fields.Monetary(string='Tiền OT', currency_field='currency_id')
    tien_phat_di_tre = fields.Monetary(string='Phạt đi trễ', currency_field='currency_id')
    tien_phat_ve_som = fields.Monetary(string='Phạt về sớm', currency_field='currency_id')
    tong_phat = fields.Monetary(string='Tổng phạt', currency_field='currency_id')
    tong_luong = fields.Monetary(string='Tổng lương', currency_field='currency_id')
    thuc_nhan = fields.Monetary(string='Thực nhận', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id.id)

    def compute_preview(self):
        """Sử dụng logic của TinhLuongBangLuongLine để tính cho 1 nhân viên."""
        self.ensure_one()
        # re-use the line computation by creating an in-memory line (not saved)
        Line = self.env['tinh_luong.bang_luong.line']
        # create temporary parent payroll to pass dates
        Payroll = self.env['tinh_luong.bang_luong']
        payroll = Payroll.new({'tu_ngay': self.tu_ngay, 'den_ngay': self.den_ngay})
        line = Line.new({'nhan_vien_id': self.nhan_vien_id.id, 'bang_luong_id': False})
        # attach a fake bang_luong reference by setting attribute for computation
        line.bang_luong_id = payroll
        # copy relevant fields from employee
        employee = self.nhan_vien_id
        HopDong = self.env['nhan_su.hop_dong']
        contract = HopDong.search([
            ('nhan_vien_id', '=', employee.id),
            ('ngay_bat_dau', '<=', self.tu_ngay),
            ('state', '=', 'active'),
            '|',
            ('ngay_ket_thuc', '=', False),
            ('ngay_ket_thuc', '>=', self.tu_ngay),
        ], limit=1)
        if contract:
            line.luong_co_ban = contract.luong_co_ban
        else:
            line.luong_co_ban = employee.luong_co_ban or 0.0

        Config = self.env['tinh_luong.cau_hinh']
        config = Config.get_config()

        line.he_so_ot = config.he_so_tang_ca_thuong or 1.0
        line.so_gio_chuan_ngay = config.so_gio_chuan_ngay or 8.0
        line.so_ngay_cong_chuan_thang = config.so_ngay_cong_chuan_thang or 26.0

        # call the compute method (works on new record instance)
        line._compute_salary_line()

        # transfer computed values to wizard
        self.luong_co_ban = line.luong_co_ban
        self.luong_gio = line.luong_gio
        self.gio_cong_thuc_te = line.gio_cong_thuc_te
        self.gio_nghi_phep_co_luong = line.gio_nghi_phep_co_luong
        self.gio_nghi_khong_luong = line.gio_nghi_khong_luong
        self.gio_ot = line.gio_ot

        self.tien_ot = line.tien_ot
        self.tien_phat_di_tre = line.tien_phat_di_tre
        self.tien_phat_ve_som = line.tien_phat_ve_som
        self.tong_phat = line.tong_phat
        self.tong_luong = line.tong_luong
        self.thuc_nhan = line.thuc_nhan
        return True
