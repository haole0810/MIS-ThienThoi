# -*- coding: utf-8 -*-
from odoo import models, fields, api
import smtplib
from email.mime.text import MIMEText
class YeuCauNhapHang(models.Model):
    _name = 'quan_ly_mua_hang.yeu_cau'
    _description = 'Yêu cầu nhập hàng Thiên Thời'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Cho phép nhắn tin và gửi mail dưới bản ghi
    _rec_name = 'ma_yeu_cau'

    ma_yeu_cau = fields.Char(string="Mã yêu cầu", readonly=True, default="Mới")
    
    # Kết nối với dữ liệu từ module thien_thoi_base
    san_pham_id = fields.Many2one('thien_thoi_base.san_pham', string="Sản phẩm thiếu", readonly=True)
    kho_id = fields.Many2one('thien_thoi_base.kho', string="Tại kho", readonly=True)
    
    so_luong_hien_tai = fields.Float(string="Tồn thực tế", readonly=True)
    muc_toi_thieu = fields.Float(string="Mức tối thiểu", readonly=True)
    so_luong_can_nhap = fields.Float(string="Số lượng cần nhập")
    
    # Phần dành cho Quản lý chọn
    nha_cung_cap_id = fields.Many2one('thien_thoi_base.nha_cung_cap', string="Nhà cung cấp", tracking=True)
    email_ncc = fields.Char(related='nha_cung_cap_id.email', string="Email liên hệ", readonly=True)
    
    state = fields.Selection([
        ('draft', 'Chờ xử lý'),
        ('sent', 'Đã gửi mail'),
        ('done', 'Đã nhập hàng'),
        ('cancel', 'Hủy bỏ')
    ], string="Trạng thái", default='draft', tracking=True)

    # Hàm tự động tạo mã yêu cầu
    @api.model
    def create(self, vals):
        if vals.get('ma_yeu_cau', 'Mới') == 'Mới':
            vals['ma_yeu_cau'] = self.env['ir.sequence'].next_by_code('quan_ly_mua_hang.yeu_cau') or 'YCNH'
        return super(YeuCauNhapHang, self).create(vals)

    def action_check_low_stock(self):
        # Lấy tất cả bản ghi tồn kho
        inventory_records = self.env['thien_thoi_base.ton_kho'].search([])
        
        for rec in inventory_records:
            # So sánh giá trị thực của 2 trường dữ liệu
            if rec.so_luong_hien_tai < rec.muc_toi_thieu:
                # Kiểm tra tránh tạo trùng yêu cầu đang chờ (draft)
                existing = self.search([
                    ('san_pham_id', '=', rec.san_pham_id.id),
                    ('kho_id', '=', rec.kho_id.id),
                    ('state', '=', 'draft')
                ])
                
                if not existing:
                    self.create({
                        'san_pham_id': rec.san_pham_id.id,
                        'kho_id': rec.kho_id.id,
                        'so_luong_hien_tai': rec.so_luong_hien_tai,
                        'muc_toi_thieu': rec.muc_toi_thieu,
                        'so_luong_can_nhap': rec.muc_toi_thieu - rec.so_luong_hien_tai,
                        'state': 'draft'
                    })
        return True

    def action_send_mail(self):
            self.ensure_one()
            
            # 1. Lấy thông tin từ cấu hình đã lưu
            get_param = self.env['ir.config_parameter'].sudo().get_param
            sender_email = get_param('quan_ly_mua_hang.sender_email')
            sender_password = get_param('quan_ly_mua_hang.sender_password')

            if not sender_email or not sender_password:
                raise UserError("Vui lòng cấu hình Email gửi đi trong phần Cài đặt!")

            # 2. Soạn nội dung HTML chuyên nghiệp
            # Dùng inline CSS để đảm bảo hiển thị tốt trên mọi trình duyệt mail
            body_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px;">
                        <h2 style="color: #004a99; text-align: center;">YÊU CẦU BÁO GIÁ</h2>
                        <p>Kính gửi quý nhà cung cấp <strong>{self.nha_cung_cap_id.ten_ncc}</strong>,</p>
                        <p>Chúng tôi là <strong>TNHH Thiên Thời</strong>. Hiện tại, chúng tôi có nhu cầu nhập thêm sản phẩm sau:</p>
                        
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <thead>
                                <tr style="background-color: #f2f2f2;">
                                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Sản phẩm</th>
                                    <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Số lượng cần</th>
                                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Đơn vị</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="border: 1px solid #ddd; padding: 12px;">{self.san_pham_id.ten_sp}</td>
                                    <td style="border: 1px solid #ddd; padding: 12px; text-align: center; color: #d9534f; font-weight: bold;">
                                        {self.so_luong_can_nhap}
                                    </td>
                                    <td style="border: 1px solid #ddd; padding: 12px;">{self.san_pham_id.don_vi_tinh}</td>
                                </tr>
                            </tbody>
                        </table>

                        <p>Vui lòng phản hồi sớm nhất về giá cả và thời gian giao hàng dự kiến.</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #777;">
                            Đây là email tự động từ hệ thống quản lý kho TNHH Thiên Thời.<br/>
                            Địa chỉ: TP. Hồ Chí Minh
                        </p>
                    </div>
                </body>
            </html>
            """

            # 3. Gửi mail bằng smtplib (Dùng MIMEText với kiểu 'html')
            msg = MIMEText(body_html, 'html', 'utf-8')
            msg['Subject'] = f"[RFQ] Yêu cầu báo giá sản phẩm {self.san_pham_id.ten_sp}"
            msg['From'] = sender_email
            msg['To'] = self.nha_cung_cap_id.email

            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [self.nha_cung_cap_id.email], msg.as_string())
                server.quit()
                
                # Lưu lại hoạt động vào Chatter để theo dõi
                self.message_post(body=f"Đã gửi email yêu cầu báo giá đến {self.nha_cung_cap_id.email}")
                self.state = 'sent'
            except Exception as e:
                raise fields.UserError(f"Lỗi khi gửi mail: {str(e)}")

            return True