{
    'name': 'Thiên Thời Base',
    'summary': 'Danh mục dùng chung: Sản phẩm, Đối tác, Kho hàng',
    'version': '1.0',
    'author': 'Lê Tấn Hào - HCMC University of Transport',
    'depends': ['base','product', 'stock'], 
    'data': [
        'security/ir.model.access.csv',
        'views/base_views.xml'
        
    ],
    'installable': True,
    'application': True,
}