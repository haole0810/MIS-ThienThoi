# -*- coding: utf-8 -*-
{
    'name': "Quản Lý Nhập Kho Thiên Thời",

    'summary': "Module quản lý nghiệp vụ nhập hàng và kiểm soát chất lượng nguyên liệu",

    'description': """
        Hệ thống quản lý nhập kho dành cho công ty Thiên Thời:
        - Tiếp nhận nguyên liệu (Bánh phôi, gia vị, bao bì) tính theo đơn vị KG.
        - Tự động gợi ý mã lô (Lot Number) theo chuẩn YYMMDD-NCC-SP.
        - Đánh giá chất lượng hàng nhập và quản lý tổng giá trị phiếu nhập.
    """,

    'author': "Lê Tấn Hào - HCMC University of Transport",
    'website': "https://ut.edu.vn",

    'category': 'Inventory',
    'version': '1.0',

    # QUAN TRỌNG: Phải thêm 'product' để sử dụng danh mục sản phẩm của Odoo
    'depends': ['base', 'product'],

    # Các file XML phải được liệt kê đúng thứ tự để Odoo load giao diện
    'data': [
        'security/ir.model.access.csv', # Mở khóa dấu thăng (#) để cấp quyền truy cập
        'views/views.xml',
    ],
    
    'installable': True,
    'application': True, # Đánh dấu là ứng dụng chính để dễ tìm trong danh sách Apps
    'auto_install': False,
}