# -*- coding: utf-8 -*-
from odoo import http

# class RoutingLocations(http.Controller):
#     @http.route('/routing_locations/routing_locations/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/routing_locations/routing_locations/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('routing_locations.listing', {
#             'root': '/routing_locations/routing_locations',
#             'objects': http.request.env['routing_locations.routing_locations'].search([]),
#         })

#     @http.route('/routing_locations/routing_locations/objects/<model("routing_locations.routing_locations"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('routing_locations.object', {
#             'object': obj
#         })