# -*- coding: utf-8 -*-
{
    'name': "Nhân sự Thiên Thời",

    'summary': "Quản lý nhân sự, chấm công, tính lương cho công ty Thiên Thời",

    'description': """
        Module quản lý nhân sự dành cho công ty Thiên Thời:
        - Quản lý thông tin nhân viên: Họ tên, ngày sinh, số điện thoại, địa chỉ, chức vụ, phòng ban.
        - Quản lý chấm công: Ghi nhận thời gian vào/ra hàng ngày, tính toán số giờ làm việc.
        - Tính lương: Dựa trên số giờ làm việc, lương cơ bản, phụ cấp và các khoản khấu trừ.
    """,

    'author': "Lê Tấn Hào",

    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'thien_thoi_base'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
}

