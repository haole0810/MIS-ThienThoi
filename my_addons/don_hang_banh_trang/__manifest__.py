# -*- coding: utf-8 -*-
{
    'name': 'Đơn Hàng Bánh Tráng',
    'version': '17.0.1.0.0',
    'summary': 'Quản lý đơn hàng xưởng bánh tráng',
    'description': """
        Module xử lý đơn hàng cho xưởng bánh tráng.
        Quy trình: Xác nhận → Đóng gói → Xuất kho → (Hủy)
    """,
    'author': 'Thiên Thời',
    'category': 'Inventory',
    'depends': [
        'base',
        'mail',
        'thien_thoi_base',
        'quan_ly_xuat',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/don_hang_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
