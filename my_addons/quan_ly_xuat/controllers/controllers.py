# -*- coding: utf-8 -*-
# from odoo import http


# class QuanLyXuat(http.Controller):
#     @http.route('/quan_ly_xuat/quan_ly_xuat', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/quan_ly_xuat/quan_ly_xuat/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('quan_ly_xuat.listing', {
#             'root': '/quan_ly_xuat/quan_ly_xuat',
#             'objects': http.request.env['quan_ly_xuat.quan_ly_xuat'].search([]),
#         })

#     @http.route('/quan_ly_xuat/quan_ly_xuat/objects/<model("quan_ly_xuat.quan_ly_xuat"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('quan_ly_xuat.object', {
#             'object': obj
#         })

