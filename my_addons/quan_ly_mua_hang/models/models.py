# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError # Quan trọng: Cần import cái này
import smtplib
from email.mime.text import MIMEText

class YeuCauNhapHang(models.Model):
    _name = 'quan_ly_mua_hang.yeu_cau'
    _description = 'Yêu cầu nhập hàng Thiên Thời'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_yeu_cau'

    ma_yeu_cau = fields.Char(string="Mã yêu cầu", readonly=True, default="Mới")
    ngay_lap = fields.Date(string="Ngày lập", default=fields.Date.context_today)
    
    # Kết nối với danh sách nhiều sản phẩm
    line_ids = fields.One2many('quan_ly_mua_hang.yeu_cau.line', 'yeu_cau_id', string="Chi tiết sản phẩm")
    
    state = fields.Selection([
        ('draft', 'Chờ xử lý'),
        ('sent', 'Đã gửi mail'),
        ('cancel', 'Hủy bỏ')
    ], string="Trạng thái", default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('ma_yeu_cau', 'Mới') == 'Mới':
            vals['ma_yeu_cau'] = self.env['ir.sequence'].next_by_code('quan_ly_mua_hang.yeu_cau') or 'YCNH'
        return super(YeuCauNhapHang, self).create(vals)

    def action_check_low_stock(self):
        """
        Quét hàng thiếu:
        - Nếu có hàng thiếu: Tạo phiếu và điền sẵn dữ liệu.
        - Nếu không có hàng thiếu: Mở một Form trống hoàn toàn để người dùng tự nhập (không tạo bản ghi rác).
        """
        inventory_records = self.env['thien_thoi_base.ton_kho'].search([])
        lines_data = [] 
        
        for rec in inventory_records:
            if rec.so_luong_hien_tai < rec.muc_toi_thieu:
                # Kiểm tra tránh trùng sản phẩm ở phiếu draft khác
                existing_line = self.env['quan_ly_mua_hang.yeu_cau.line'].search([
                    ('san_pham_id', '=', rec.san_pham_id.id),
                    ('yeu_cau_id.state', '=', 'draft')
                ])
                
                if not existing_line:
                    lines_data.append((0, 0, {
                        'san_pham_id': rec.san_pham_id.id,
                        'kho_id': rec.kho_id.id,
                        'so_luong_hien_tai': rec.so_luong_hien_tai,
                        'muc_toi_thieu': rec.muc_toi_thieu,
                        'so_luong_can_nhap': rec.muc_toi_thieu - rec.so_luong_hien_tai,
                    }))

        if lines_data:
            # TRƯỜNG HỢP 1: Có hàng thiếu -> Tạo phiếu gom nhóm
            new_request = self.create({
                'line_ids': lines_data,
                'state': 'draft'
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'quan_ly_mua_hang.yeu_cau',
                'view_mode': 'form',
                'res_id': new_request.id,
                'target': 'current',
            }
        else:
            # TRƯỜNG HỢP 2: Không có hàng thiếu -> Mở Form trắng để tự nhập
            # Chúng ta trả về hành động mở Form ở chế độ 'new' (không lưu ID vào DB trước)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Tạo phiếu nhập hàng mới',
                'res_model': 'quan_ly_mua_hang.yeu_cau',
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_state': 'draft'}, # Thiết lập trạng thái mặc định
            }
    def action_send_bulk_mail(self):
            """Bộ xử lý thông minh: Gom các sản phẩm cùng nhà cung cấp vào 1 email duy nhất"""
            self.ensure_one()
            
            # 1. Lấy cấu hình SMTP
            get_param = self.env['ir.config_parameter'].sudo().get_param
            sender_email = get_param('quan_ly_mua_hang.sender_email')
            sender_password = get_param('quan_ly_mua_hang.sender_password')

            if not sender_email or not sender_password:
                raise UserError("Vui lòng cấu hình Email gửi đi trong Cài đặt!")

            if not self.line_ids:
                raise UserError("Không có sản phẩm nào để gửi!")

            # 2. Thuật toán Gom nhóm sản phẩm theo Email NCC
            # Cấu trúc: { 'email_ncc_1': [line1, line2], 'email_ncc_2': [line3] }
            grouped_lines = {}
            for line in self.line_ids:
                if line.nha_cung_cap_id and line.nha_cung_cap_id.email:
                    email = line.nha_cung_cap_id.email
                    if email not in grouped_lines:
                        grouped_lines[email] = []
                    grouped_lines[email].append(line)

            if not grouped_lines:
                raise UserError("Không tìm thấy nhà cung cấp hoặc email hợp lệ trong các dòng sản phẩm!")

            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(sender_email, sender_password)

                for email, lines in grouped_lines.items():
                    ncc_name = lines[0].nha_cung_cap_id.ten_ncc # Lấy tên NCC từ dòng đầu tiên
                    
                    # 3. Tạo bảng danh sách sản phẩm cho email này
                    table_rows = ""
                    for line in lines:
                        table_rows += f"""
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 8px;">{line.san_pham_id.ten_sp}</td>
                                <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{line.so_luong_can_nhap}</td>
                                <td style="border: 1px solid #ddd; padding: 8px;">{line.san_pham_id.don_vi_tinh}</td>
                            </tr>
                        """

                    body_html = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif;">
                            <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px;">
                                <h2 style="color: #004a99; text-align: center;">YÊU CẦU BÁO GIÁ</h2>
                                <p>Kính gửi: <strong>{ncc_name}</strong>,</p>
                                <p>Công ty TNHH Thiên Thời cần báo giá cho các mặt hàng sau:</p>
                                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                                    <tr style="background: #f2f2f2;">
                                        <th style="border: 1px solid #ddd; padding: 10px;">Sản phẩm</th>
                                        <th style="border: 1px solid #ddd; padding: 10px;">Số lượng</th>
                                        <th style="border: 1px solid #ddd; padding: 10px;">ĐVT</th>
                                    </tr>
                                    {table_rows}
                                </table>
                                <p style="margin-top: 20px;">Vui lòng phản hồi sớm nhất. Trân trọng!</p>
                            </div>
                        </body>
                    </html>
                    """

                    msg = MIMEText(body_html, 'html', 'utf-8')
                    msg['Subject'] = f"[RFQ] Yêu cầu báo giá nhiều sản phẩm - {self.ma_yeu_cau}"
                    msg['From'] = sender_email
                    msg['To'] = email

                    server.sendmail(sender_email, [email], msg.as_string())
                    
                    # Log lại thông tin gửi thành công
                    sp_names = ", ".join([l.san_pham_id.ten_sp for l in lines])
                    self.message_post(body=f"Đã gửi email gom nhóm cho {ncc_name} ({email}). Sản phẩm: {sp_names}")

                server.quit()
                self.state = 'sent'
            except Exception as e:
                raise UserError(f"Lỗi khi gửi mail: {str(e)}")

class YeuCauNhapHangLine(models.Model):
    _name = 'quan_ly_mua_hang.yeu_cau.line'
    _description = 'Chi tiết dòng yêu cầu'

    yeu_cau_id = fields.Many2one('quan_ly_mua_hang.yeu_cau', ondelete='cascade')
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string="Sản phẩm", required=True)
    kho_id = fields.Many2one('thien_thoi_base.kho', string="Tại kho")
    so_luong_hien_tai = fields.Float(string="Tồn thực tế")
    muc_toi_thieu = fields.Float(string="Mức tối thiểu")
    so_luong_can_nhap = fields.Float(string="Số lượng cần")
    nha_cung_cap_id = fields.Many2one('thien_thoi_base.nha_cung_cap', string="Nhà cung cấp")
    email_ncc = fields.Char(related='nha_cung_cap_id.email', readonly=True)