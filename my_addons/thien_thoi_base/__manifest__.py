{
    'name': 'Thiên Thời Base',
    'summary': 'Danh mục dùng chung: Sản phẩm, Đối tác, Kho hàng',
    'version': '1.0',
    'author': 'Lê Tấn Hào - HCMC University of Transport',
    'depends': ['base','product', 'stock'], # stock để dùng các tính năng kho gốc
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/partner_views.xml'
    ],
    'installable': True,
    'application': True,
}