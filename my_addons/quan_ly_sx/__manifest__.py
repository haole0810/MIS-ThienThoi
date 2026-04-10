{
    'name': 'Sản xuất Thiên Thời',
    'version': '1.0',
    'author': 'Nguyễn Hải Việt - University of Transport',
    'category': 'Manufacturing',
    # THÊM 'mail' VÀO ĐÂY NÈ VIỆT
    'depends': ['base', 'mail', 'thien_thoi_base'], 
    'data': [
        'security/ir.model.access.csv',
        'views/production_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3', # Thêm dòng này cho đỡ báo Warning màu vàng nha
}