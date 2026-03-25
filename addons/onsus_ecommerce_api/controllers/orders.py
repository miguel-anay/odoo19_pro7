import json
from odoo import http
from odoo.http import request, Response


class OrdersController(http.Controller):

    def _cors_headers(self):
        return [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Content-Type', 'application/json'),
        ]

    def _json_response(self, data, status=200):
        return Response(
            json.dumps(data, default=str),
            status=status,
            headers=self._cors_headers(),
        )

    @http.route('/api/shop/orders', auth='none', methods=['OPTIONS'], csrf=False)
    def options(self, **kwargs):
        return Response(status=204, headers=self._cors_headers())

    @http.route('/api/shop/orders', auth='user', methods=['GET'], csrf=False)
    def get_orders(self, **kwargs):
        """Return confirmed sale orders for the authenticated user."""
        try:
            partner = request.env.user.partner_id
            orders = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sale', 'done']),
            ], order='date_order desc')

            result = []
            for order in orders:
                lines = []
                for line in order.order_line:
                    lines.append({
                        'id': line.id,
                        'product_name': line.product_id.name,
                        'qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'subtotal': line.price_subtotal,
                    })
                result.append({
                    'id': order.id,
                    'name': order.name,
                    'date': str(order.date_order),
                    'state': order.state,
                    'state_label': dict(order._fields['state'].selection).get(order.state, order.state),
                    'amount_total': order.amount_total,
                    'currency': order.currency_id.name,
                    'lines': lines,
                })
            return self._json_response({'orders': result})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)
