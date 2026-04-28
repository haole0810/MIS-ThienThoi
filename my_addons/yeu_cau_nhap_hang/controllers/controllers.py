# -*- coding: utf-8 -*-
# from odoo import http


# class YeuCauNhapHang(http.Controller):
#     @http.route('/yeu_cau_nhap_hang/yeu_cau_nhap_hang', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/yeu_cau_nhap_hang/yeu_cau_nhap_hang/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('yeu_cau_nhap_hang.listing', {
#             'root': '/yeu_cau_nhap_hang/yeu_cau_nhap_hang',
#             'objects': http.request.env['yeu_cau_nhap_hang.yeu_cau_nhap_hang'].search([]),
#         })

#     @http.route('/yeu_cau_nhap_hang/yeu_cau_nhap_hang/objects/<model("yeu_cau_nhap_hang.yeu_cau_nhap_hang"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('yeu_cau_nhap_hang.object', {
#             'object': obj
#         })

