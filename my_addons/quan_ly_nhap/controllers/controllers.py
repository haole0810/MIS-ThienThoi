# -*- coding: utf-8 -*-
# from odoo import http


# class QuanLyNhap(http.Controller):
#     @http.route('/quan_ly_nhap/quan_ly_nhap', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/quan_ly_nhap/quan_ly_nhap/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('quan_ly_nhap.listing', {
#             'root': '/quan_ly_nhap/quan_ly_nhap',
#             'objects': http.request.env['quan_ly_nhap.quan_ly_nhap'].search([]),
#         })

#     @http.route('/quan_ly_nhap/quan_ly_nhap/objects/<model("quan_ly_nhap.quan_ly_nhap"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('quan_ly_nhap.object', {
#             'object': obj
#         })

