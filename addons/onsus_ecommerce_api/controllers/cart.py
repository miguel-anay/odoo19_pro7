import json
from odoo import http
from odoo.http import request, Response


class CartController(http.Controller):

    def _cors_headers(self):
        return [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Content-Type', 'application/json'),
        ]

    def _json_response(self, data, status=200):
        return Response(
            json.dumps(data),
            status=status,
            headers=self._cors_headers(),
        )

    def _get_or_create_cart(self):
        """Get the current user's draft sale order (cart) or create one."""
        SaleOrder = request.env['sale.order'].sudo()
        partner = request.env.user.partner_id
        cart = SaleOrder.search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft'),
        ], limit=1)
        if not cart:
            cart = SaleOrder.create([{
                'partner_id': partner.id,
                'state': 'draft',
            }])
        return cart

    def _cart_to_dict(self, order):
        lines = []
        for line in order.order_line:
            product = line.product_id
            lines.append({
                'id': line.id,
                'product_id': product.product_tmpl_id.id,
                'variant_id': product.id,
                'name': product.name,
                'qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'subtotal': line.price_subtotal,
            })
        return {
            'id': order.id,
            'lines': lines,
            'amount_untaxed': order.amount_untaxed,
            'amount_tax': order.amount_tax,
            'amount_total': order.amount_total,
        }

    @http.route(['/api/shop/cart', '/api/shop/cart/line'], auth='none', methods=['OPTIONS'], csrf=False)
    def options(self, **kwargs):
        return Response(status=204, headers=self._cors_headers())

    @http.route('/api/shop/cart', auth='user', methods=['GET'], csrf=False)
    def get_cart(self, **kwargs):
        try:
            cart = self._get_or_create_cart()
            return self._json_response({'cart': self._cart_to_dict(cart)})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/shop/cart/line', auth='user', methods=['POST'], csrf=False)
    def add_or_update_line(self, **kwargs):
        """
        Body JSON:
          product_id  — product.template id
          variant_id  — product.product id (optional, uses first variant)
          qty         — quantity (float, required)
          line_id     — existing line id to update (optional)
        """
        try:
            body = json.loads(request.httprequest.data or '{}')
            qty = float(body.get('qty', 1))
            line_id = body.get('line_id')
            cart = self._get_or_create_cart()

            if line_id:
                line = request.env['sale.order.line'].sudo().browse(int(line_id))
                if line.exists() and line.order_id == cart:
                    if qty <= 0:
                        line.unlink()
                    else:
                        line.write({'product_uom_qty': qty})
                else:
                    return self._json_response({'error': 'Line not found in cart'}, status=404)
            else:
                variant_id = body.get('variant_id')
                product_tmpl_id = body.get('product_id')
                if not variant_id and not product_tmpl_id:
                    return self._json_response({'error': 'product_id or variant_id required'}, status=400)

                if not variant_id:
                    tmpl = request.env['product.template'].sudo().browse(int(product_tmpl_id))
                    if not tmpl.exists():
                        return self._json_response({'error': 'Product not found'}, status=404)
                    variant_id = tmpl.product_variant_id.id

                request.env['sale.order.line'].sudo().create([{
                    'order_id': cart.id,
                    'product_id': int(variant_id),
                    'product_uom_qty': qty,
                }])

            return self._json_response({'cart': self._cart_to_dict(cart)})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/shop/cart/line', auth='user', methods=['DELETE'], csrf=False)
    def remove_line(self, **kwargs):
        try:
            body = json.loads(request.httprequest.data or '{}')
            line_id = body.get('line_id')
            if not line_id:
                return self._json_response({'error': 'line_id required'}, status=400)
            cart = self._get_or_create_cart()
            line = request.env['sale.order.line'].sudo().browse(int(line_id))
            if line.exists() and line.order_id == cart:
                line.unlink()
            return self._json_response({'cart': self._cart_to_dict(cart)})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)
