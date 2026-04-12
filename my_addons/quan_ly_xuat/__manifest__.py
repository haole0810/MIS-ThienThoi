# -*- coding: utf-8 -*-
{
    'name': "Quản lý Xuất Kho Thiên Thời",
    'summary': "Quản lý phiếu xuất kho, kiểm tra tồn và cảnh báo nhập hàng khi thiếu",
    'description': """
        Module quản lý xuất kho của Thiên Thời:
        - Tạo phiếu xuất kho với trạng thái Nháp, Đóng gói, Xuất kho.
        - Kiểm tra tồn kho trước khi xuất.
        - Tự động trừ tồn kho và tạo cảnh báo khi tồn kho thấp dưới mức tối thiểu.
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

