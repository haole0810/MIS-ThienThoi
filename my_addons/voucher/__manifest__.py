# -*- coding: utf-8 -*-
{
    'name': 'Quản lý Voucher',
    'version': '1.0',
    'summary': 'Module quản lý mã giảm giá cho Đơn Hàng Bánh Tráng',
    'sequence': 10,
    'description': """
        Quản lý mã giảm giá (Voucher), áp dụng giảm tiền mặt hoặc phần trăm 
        dựa trên số lượng tối thiểu của đơn hàng.
    """,
    'category': 'Sales',
    'author': 'Bạn',
    'depends': ['base', 'don_hang_banh_trang'], # Bắt buộc phải kế thừa don_hang_banh_trang
    'data': [
        'security/ir.model.access.csv', # Load file phân quyền trước
        'views/voucher_views.xml',      # Giao diện tạo voucher
        'views/don_hang_inherit_views.xml', # Giao diện kế thừa đơn hàng
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}