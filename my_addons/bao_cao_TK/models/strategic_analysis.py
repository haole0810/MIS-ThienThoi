from odoo import models, fields, api, _
from datetime import timedelta
import random


class StrategicAnalysis(models.Model):
    _name = 'strategic.analysis'
    _description = 'Trung tâm Phân tích Chiến lược'

    name = fields.Char(default="DSS Dashboard")

    date_from = fields.Date(default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(default=fields.Date.today)

    product_ids = fields.Many2many('thien_thoi_base.san_pham')
    employee_ids = fields.Many2many('res.users')  # 🔥 đổi sang res.users cho đồng bộ
    kho_id = fields.Many2one('thien_thoi_base.kho')
    ai_suggestions = fields.Text(string="Tóm tắt hệ thống")
    # Trường liên kết với các gợi ý chi tiết
    suggestion_ids = fields.One2many('strategic.suggestion', 'analysis_id', string="Đề xuất chi tiết")
    # ================= DEMO DATA =================
    def generate_demo_data(self):
        # 1. LẤY DỮ LIỆU NỀN
        products = self.env['thien_thoi_base.san_pham'].search([])
        # Chỗ này cực kỳ quan trọng: Lấy thẳng từ bảng nhân viên của bạn
        employees = self.env['nhan_su.nhan_vien'].search([])

        if not products or not employees:
            raise models.ValidationError("Vui lòng tạo ít nhất 1 sản phẩm và 1 nhân viên trong hồ sơ nhân sự trước!")

        # 2. TẠO 3 KHO DEMO (Nếu chưa có)
        danh_sach_kho = [
            {'ma': 'K01', 'ten': 'Kho Quận 12'},
            {'ma': 'K02', 'ten': 'Kho Vũng Tàu'},
            {'ma': 'K03', 'ten': 'Kho Đà Lạt'},
        ]
        kho_ids = []
        for k in danh_sach_kho:
            k_obj = self.env['thien_thoi_base.kho'].search([('ten_kho', '=', k['ten'])], limit=1)
            if not k_obj:
                k_obj = self.env['thien_thoi_base.kho'].create({'ma_kho': k['ma'], 'ten_kho': k['ten']})
            kho_ids.append(k_obj.id)

        # 3. DỌN DẸP DỮ LIỆU CŨ CHO SẠCH
        self.env['don_hang_banh_trang.don_hang'].search([('ten_khach_hang', 'like', 'KH Demo')]).unlink()
        self.env['nhan_su.cham_cong'].search([]).unlink()
        self.env['phieu.san.xuat'].search([('name', 'like', 'SX-DEMO-')]).unlink()
        self.env['thien_thoi_base.ton_kho'].search([]).unlink() # Xóa hẳn nạp lại cho mới

        # 4. NẠP DỮ LIỆU "ĐẠI" ĐỂ THỐNG KÊ
        count = 0
        
        # --- Nạp Tồn Kho (Cho đại số lượng vào 3 kho) ---
        for k_id in kho_ids:
            for p in products:
                self.env['thien_thoi_base.ton_kho'].create({
                    'san_pham_id': p.id,
                    'kho_id': k_id,
                    'so_luong_hien_tai': random.randint(50, 500), # Cho đại từ 50-500kg
                    'muc_toi_thieu': 100
                })

        # --- Nạp Đơn hàng & Chấm công & Sản xuất cho nhân viên ---
        for emp in employees:
            for i in range(5): # Mỗi nhân viên nạp đại 5 bản ghi
                count += 1
                date_ref = fields.Date.today() - timedelta(days=random.randint(0, 30))
                p = random.choice(products)
                k = random.choice(kho_ids)

                # Đơn hàng
                self.env['don_hang_banh_trang.don_hang'].create({
                    'ten_khach_hang': f'KH Demo {count}',
                    'kho_id': k,
                    'ngay_tao': date_ref,
                    'trang_thai': 'xuat_kho'
                })

                # Chấm công (Dùng đúng emp.id để không lỗi)
                self.env['nhan_su.cham_cong'].create({
                    'nhan_vien_id': emp.id,
                    'ngay': date_ref,
                    'trang_thai': random.choice(['di_tre', 've_som', 'vi_pham', 'binh_thuong']),
                })

                # Sản xuất
                self.env['phieu.san.xuat'].create({
                    'name': f'SX-DEMO-{count}',
                    'product_id': p.id,
                    'so_luong': random.randint(100, 200),
                    'so_luong_thanh_pham_dat': random.randint(80, 95),
                    'loai_phieu': random.choice(['lua', 'tron', 'sot']),
                    'trang_thai': 'xong',
                    'ngay_tao': date_ref,
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Xong!',
                'message': 'Đã nạp 3 kho và dữ liệu thống kê đại diện.',
                'type': 'success',
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }
    def action_run_analysis(self):

        # Xóa dữ liệu cũ
        self.env['strategic.suggestion'].search([
            ('analysis_id', '=', self.id),
            ('trang_thai', '=', 'draft')
        ]).unlink()

        domain_date = [
            ('ngay_tao', '>=', self.date_from),
            ('ngay_tao', '<=', self.date_to),
        ]

        # ================= 1. KPI TỔNG =================
        orders = self.env['don_hang_banh_trang.don_hang'].search(domain_date)
        total_orders = len(orders)
        total_revenue = sum(orders.mapped('tong_tien'))

        sx = self.env['phieu.san.xuat'].search([
            ('trang_thai', '=', 'xong'),
            *domain_date
        ])
        total_qty = sum(sx.mapped('so_luong'))
        avg_loss = sum(sx.mapped('hao_hut')) / len(sx) if sx else 0

        cc = self.env['nhan_su.cham_cong'].search([
            ('trang_thai', 'in', ['di_tre', 've_som', 'vi_pham']),
            ('ngay', '>=', self.date_from),
            ('ngay', '<=', self.date_to),
        ])
        total_violation = len(cc)

        self.env['strategic.suggestion'].create({
            'analysis_id': self.id,
            'name': '📊 BÁO CÁO TỔNG QUAN',
            'description': (f"• Đơn: {total_orders}\n"
                            f"• Doanh thu: {total_revenue:,.0f} VNĐ\n"
                            f"• Sản lượng: {total_qty}\n"
                            f"• Hao hụt TB: {avg_loss:.1f}%\n"
                            f"• Vi phạm: {total_violation}"),
            'type': 'info'
        })

        # ================= 2. NHÂN VIÊN =================

        # Hiệu suất (Top 3)
        sx_nv = self.env['phieu.san.xuat'].read_group(
            domain=[('trang_thai', '=', 'xong'), *domain_date],
            fields=['create_uid', 'so_luong:sum', 'hao_hut:avg'],
            groupby=['create_uid'],
            orderby='so_luong desc',
            limit=3
        )

        for r in sx_nv:
            if r['create_uid']:
                self.env['strategic.suggestion'].create({
                    'analysis_id': self.id,
                    'name': f'🏆 Nhân viên xuất sắc: {r["create_uid"][1]}',
                    'description': f'Sản lượng cao ({r["so_luong"]}) | Hao hụt thấp ({r["hao_hut"]:.1f}%)',
                    'type': 'success'
                })

        # Vi phạm
        cc_group = self.env['nhan_su.cham_cong'].read_group(
            domain=[
                ('trang_thai', 'in', ['di_tre', 've_som', 'vi_pham']),
                ('ngay', '>=', self.date_from),
                ('ngay', '<=', self.date_to),
            ],
            fields=['nhan_vien_id'],
            groupby=['nhan_vien_id']
        )

        for r in cc_group:
            count = r.get('nhan_vien_id_count') or r.get('__count') or 0
            if count >= 3:
                self.env['strategic.suggestion'].create({
                    'analysis_id': self.id,
                    'name': f'⚠️ Kỷ luật: {r["nhan_vien_id"][1]}',
                    'description': f'{count} lần vi phạm trong tuần',
                    'type': 'danger'
                })

        # ================= 3. SẢN PHẨM =================
        domain_date_ctdh = [
            ('ngay_tao_don', '>=', self.date_from),
            ('ngay_tao_don', '<=', self.date_to),
        ]

        # Doanh thu theo sản phẩm
        revenue_sp = self.env['don_hang_banh_trang.chi_tiet_don_hang'].read_group(
            domain=domain_date_ctdh,
            fields=['san_pham_id', 'thanh_tien:sum'],
            groupby=['san_pham_id']
        )

        # Hao hụt sản xuất
        loss_sp = self.env['phieu.san.xuat'].read_group(
            domain=[('trang_thai', '=', 'xong'), *domain_date],
            fields=['product_id', 'hao_hut:avg'],
            groupby=['product_id']
        )

        # Tồn kho
        stock_sp = self.env['thien_thoi_base.ton_kho'].read_group(
            domain=[],
            fields=['san_pham_id', 'so_luong_hien_tai:sum'],
            groupby=['san_pham_id']
        )

        # Map dữ liệu
        loss_map = {r['product_id'][0]: r['hao_hut'] for r in loss_sp if r['product_id']}
        stock_map = {r['san_pham_id'][0]: r['so_luong_hien_tai'] for r in stock_sp if r['san_pham_id']}

        for r in revenue_sp:
            if not r['san_pham_id']:
                continue

            sp_id = r['san_pham_id'][0]
            name = r['san_pham_id'][1]
            revenue = r['thanh_tien']
            loss = loss_map.get(sp_id, 0)
            stock = stock_map.get(sp_id, 0)

            # 1. TIỀM NĂNG
            if revenue > 1000000 and loss < 7:
                self.env['strategic.suggestion'].create({
                    'analysis_id': self.id,
                    'name': f'🚀 Tiềm năng: {name}',
                    'description': 'Doanh thu cao, hao hụt thấp → nên đẩy mạnh',
                    'type': 'success'
                })

            # 2. TĂNG SẢN XUẤT
            elif revenue > 1000000 and stock < 50:
                self.env['strategic.suggestion'].create({
                    'analysis_id': self.id,
                    'name': f'📈 Tăng sản xuất: {name}',
                    'description': 'Doanh thu cao nhưng tồn kho thấp',
                    'type': 'warning'
                })

            # 3. CẢNH BÁO
            elif revenue < 500000 and stock > 100:
                self.env['strategic.suggestion'].create({
                    'analysis_id': self.id,
                    'name': f'⚠️ Cảnh báo tồn kho: {name}',
                    'description': 'Doanh thu thấp nhưng tồn kho cao',
                    'type': 'danger'
                })

        # ================= DONE =================

        if hasattr(self, 'ai_suggestions'):
            self.ai_suggestions = f"Cập nhật lúc {fields.Datetime.now()}"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': 'Đã cập nhật phân tích mới',
                'type': 'success',
                'sticky': False,
            }
        }
class StrategicDashboard(models.Model):
    _name = 'strategic.dashboard'
    _description = 'Dashboard'

class StrategicSuggestion(models.Model):
    _name = 'strategic.suggestion'
    _description = 'Chi tiết gợi ý chiến lược'

    # Đảm bảo trường này có mặt
    trang_thai = fields.Selection([
        ('draft', 'Đề xuất'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], default='draft', string="Trạng thái")

    # Các trường khác bạn đã có
    name = fields.Char(required=True)
    description = fields.Text()
    type = fields.Selection([
        ('success', 'Tốt'),
        ('info', 'Thông tin'),
        ('warning', 'Cảnh báo'),
        ('danger', 'Khẩn cấp')
    ], default='info')
    analysis_id = fields.Many2one('strategic.analysis', ondelete='cascade')

    def action_approve(self):
        self.write({'trang_thai': 'approved'})

    def action_reject(self):
        self.write({'trang_thai': 'rejected'})