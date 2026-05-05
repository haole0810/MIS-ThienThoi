{
    'name': 'Quản lý Chiến lược Thiên Thời',
    'version': '1.0',
    'category': 'Business Intelligence',
    'depends': [
        'base',
        'thien_thoi_base',
        'quan_ly_sx',
        'nhan_su',
        'don_hang_banh_trang',
        'quan_ly_xuat',
        'voucher',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/strategic_dashboard.xml',
    ],
    'installable': True,
    'application': True,
}