# -*- coding: utf-8 -*-
{
    'name': "Quản lý Xuất Kho Thiên Thời",
    'summary': "Quản lý phiếu xuất kho với quy trình đơn giản",
    'description': """
        Module quản lý xuất kho của Thiên Thời:
        - Tạo phiếu xuất kho với trạng thái Nháp và Đã xác nhận.
        - Thêm trường Lý do xuất để ghi chú.
        - Quy trình đơn giản hóa, loại bỏ cảnh báo nhập hàng.
    """,
    'author': "Nguyễn Công Phúc",
    'category': 'Inventory',
    'version': '1.0',
    'depends': ['base', 'thien_thoi_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

