# -*- coding: utf-8 -*-
{
    'name': "yeu_cau_nhap_hang",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Le Tan Hao - HCMC University of Transport",
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
# Sửa lại phần depends trong __manifest__.py
    'depends': ['base', 'thien_thoi_base', 'quan_ly_nhap'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/cron_data.xml', # Chúng ta sẽ tạo file này sau
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
}

