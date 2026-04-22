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

    'depends': ['base', 'thien_thoi_base','barcodes'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/ir_sequence_data.xml',
    ],
    
    'installable': True,
    'application': True, 
    'auto_install': False,
    'assets': {
    'web.assets_backend': [
        
        'quan_ly_nhap/static/src/js/mobile.js',
        'quan_ly_nhap/static/src/xml/mobile_template.xml',
    ],
    },
}