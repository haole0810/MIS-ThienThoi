# -*- coding: utf-8 -*-
# from odoo import http


# class QuanLyMuaHang(http.Controller):
#     @http.route('/quan_ly_mua_hang/quan_ly_mua_hang', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/quan_ly_mua_hang/quan_ly_mua_hang/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('quan_ly_mua_hang.listing', {
#             'root': '/quan_ly_mua_hang/quan_ly_mua_hang',
#             'objects': http.request.env['quan_ly_mua_hang.quan_ly_mua_hang'].search([]),
#         })

#     @http.route('/quan_ly_mua_hang/quan_ly_mua_hang/objects/<model("quan_ly_mua_hang.quan_ly_mua_hang"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('quan_ly_mua_hang.object', {
#             'object': obj
#         })

