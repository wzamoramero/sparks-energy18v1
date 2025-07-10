# -*- coding: utf-8 -*-
# from odoo import http


# class Sparks(http.Controller):
#     @http.route('/sparks/sparks', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sparks/sparks/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sparks.listing', {
#             'root': '/sparks/sparks',
#             'objects': http.request.env['sparks.sparks'].search([]),
#         })

#     @http.route('/sparks/sparks/objects/<model("sparks.sparks"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sparks.object', {
#             'object': obj
#         })
