{
    'name': 'Quản Lý Đơn Hàng Thiên Thời',
    'version': '1.0',
    'summary': 'Xử lý đơn hàng, đóng gói và xuất kho',
    'author': 'Lê Tấn Hào - HCMC University of Transport',
    'depends': ['base', 'thien_thoi_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/don_hang_views.xml',
    ],
    'installable': True,
    'application': True,
}