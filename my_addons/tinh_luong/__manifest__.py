# -*- coding: utf-8 -*-
{
    'name': 'Tính lương Thiên Thời',
    'summary': 'Tính lương theo nhân sự, chấm công và nghỉ phép',
    'description': '''
Module tính lương cơ bản cho Odoo 17:
- Liên kết trực tiếp với nhân sự nhan_su.nhan_vien.
- Lấy dữ liệu chấm công và nghỉ phép để tạo bảng lương theo kỳ.
- Tính lương theo giờ/công, phụ cấp, tăng ca và phạt đi trễ/về sớm.
''',
    'author': 'GitHub Copilot',
    'category': 'Human Resources',
    'version': '17.0.1.0.0',
    'depends': ['base', 'nhan_su', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/mail_template.xml',
        'views/nhan_vien_views.xml',
        'views/tinh_luong_views.xml',
        'views/tinh_luong_preview_views.xml',
        'views/cau_hinh_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
