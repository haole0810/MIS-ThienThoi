# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from datetime import datetime

class NhanSuController(http.Controller):

    @http.route('/nhan_su/api/cham_cong', type='json', auth='none', methods=['POST'], csrf=False)
    def api_check_in_out(self, **post):
        # 1. Lấy dữ liệu từ JSON gửi lên
        data = post
        
        ma_nv_tu_may = data.get('ma_nv')

        time_str = data.get('timestamp') # Định dạng: '2024-03-20 08:00:00'
        action = data.get('action')      # 'check_in' hoặc 'check_out'

        if not ma_nv_tu_may or not time_str or not action:
            return {'status': 'error', 'message': 'Dữ liệu JSON không đầy đủ'}

        # 2. Tìm nhân viên theo mã nhân viên
        nhan_vien = request.env['nhan_su.nhan_vien'].sudo().search([('ma_nv', '=', ma_nv_tu_may)], limit=1)
        if not nhan_vien:
            return {'status': 'error', 'message': 'Không tìm thấy nhân viên với mã này'}

        # Chuyển đổi chuỗi thời gian
        try:
            check_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            today = check_time.date()
        except ValueError:
            return {'status': 'error', 'message': 'Định dạng thời gian sai (Y-m-d H:M:S)'}

        # 3. Xử lý ghi nhận vào Database
        # Tìm bản ghi của nhân viên đó trong ngày hôm nay
        attendance = request.env['nhan_su.cham_cong'].sudo().search([
            ('nhan_vien_id', '=', nhan_vien.id),
            ('ngay', '=', today)
        ], limit=1)

        if action == 'check_in':
            if attendance:
                return {'status': 'warning', 'message': 'Nhân viên này đã check-in hôm nay rồi'}
            
            request.env['nhan_su.cham_cong'].sudo().create({
                'nhan_vien_id': nhan_vien.id,
                'ngay': today,
                'gio_vao': check_time,
            })
            return {'status': 'success', 'message': f'Check-in thành công cho {nhan_vien.name}'}

        elif action == 'check_out':
            if not attendance:
                return {'status': 'error', 'message': 'Không tìm thấy dữ liệu Check-in hôm nay'}
            
            attendance.sudo().write({'gio_ra': check_time})
            return {'status': 'success', 'message': f'Check-out thành công cho {nhan_vien.name}'}

        return {'status': 'error', 'message': 'Hành động không hợp lệ'}