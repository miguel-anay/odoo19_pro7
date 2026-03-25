import json
from odoo import http
from odoo.http import request, Response


class WishlistController(http.Controller):

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

    @http.route('/api/shop/wishlist', auth='none', methods=['OPTIONS'], csrf=False)
    def options(self, **kwargs):
        return Response(status=204, headers=self._cors_headers())

    @http.route('/api/shop/wishlist', auth='user', methods=['GET'], csrf=False)
    def get_wishlist(self, **kwargs):
        """Return wishlist stored in user session."""
        try:
            wishlist = request.session.get('onsus_wishlist', [])
            products = []
            if wishlist:
                tmpl_ids = [int(pid) for pid in wishlist]
                records = request.env['product.template'].sudo().browse(tmpl_ids)
                for p in records.filtered('active'):
                    image_url = (
                        f'/web/image/product.template/{p.id}/image_1920'
                        if p.image_1920 else None
                    )
                    products.append({
                        'id': p.id,
                        'name': p.name,
                        'price': p.list_price,
                        'image_url': image_url,
                    })
            return self._json_response({'wishlist': products})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/shop/wishlist', auth='user', methods=['POST'], csrf=False)
    def add_to_wishlist(self, **kwargs):
        try:
            body = json.loads(request.httprequest.data or '{}')
            product_id = body.get('product_id')
            if not product_id:
                return self._json_response({'error': 'product_id required'}, status=400)
            wishlist = request.session.get('onsus_wishlist', [])
            if product_id not in wishlist:
                wishlist.append(int(product_id))
                request.session['onsus_wishlist'] = wishlist
            return self._json_response({'wishlist_ids': wishlist})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/shop/wishlist', auth='user', methods=['DELETE'], csrf=False)
    def remove_from_wishlist(self, **kwargs):
        try:
            body = json.loads(request.httprequest.data or '{}')
            product_id = int(body.get('product_id', 0))
            wishlist = request.session.get('onsus_wishlist', [])
            wishlist = [pid for pid in wishlist if pid != product_id]
            request.session['onsus_wishlist'] = wishlist
            return self._json_response({'wishlist_ids': wishlist})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)
