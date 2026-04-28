# -*- coding: utf-8 -*-
# from odoo import http


# class ThienThoiHr(http.Controller):
#     @http.route('/thien_thoi_hr/thien_thoi_hr', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/thien_thoi_hr/thien_thoi_hr/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('thien_thoi_hr.listing', {
#             'root': '/thien_thoi_hr/thien_thoi_hr',
#             'objects': http.request.env['thien_thoi_hr.thien_thoi_hr'].search([]),
#         })

#     @http.route('/thien_thoi_hr/thien_thoi_hr/objects/<model("thien_thoi_hr.thien_thoi_hr"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('thien_thoi_hr.object', {
#             'object': obj
#         })

