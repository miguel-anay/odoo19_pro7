import json
from odoo import http
from odoo.http import request, Response


class ShopController(http.Controller):

    # ── Helper ────────────────────────────────────────────────────────────────

    def _cors_headers(self):
        return [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Content-Type', 'application/json'),
        ]

    def _json_response(self, data, status=200):
        return Response(
            json.dumps(data),
            status=status,
            headers=self._cors_headers(),
        )

    # All fields returned by default; callers can pass a set to restrict output.
    _PRODUCT_ALL_FIELDS = frozenset({
        'id', 'name', 'description', 'price', 'website_price', 'currency',
        'image_url', 'category_id', 'category_name',
        'in_stock', 'qty_available', 'active', 'is_published',
        'website_description', 'seo_name', 'website_meta_title',
        'website_meta_description', 'ribbon',
    })

    def _product_to_dict(self, product, fields=None):
        """Serialize a product.template record to a JSON-safe dict.

        Uses website_sale fields when available (is_published, website_price,
        public categories, SEO, ribbon).

        Args:
            product: product.template recordset row
            fields: optional set/list of field names to include.
                    Defaults to all fields when None.
        """
        include = self._PRODUCT_ALL_FIELDS if fields is None else frozenset(fields)

        image_url = (
            f'/web/image/product.template/{product.id}/image_1920'
            if product.image_1920 else None
        )

        # website_sale: use public category if available, fallback to internal
        has_public_categ = hasattr(product, 'public_categ_ids') and product.public_categ_ids
        if has_public_categ:
            categ = product.public_categ_ids[0]
            categ_id = categ.id
            categ_name = categ.name
        else:
            categ_id = product.categ_id.id if product.categ_id else None
            categ_name = product.categ_id.name if product.categ_id else None

        # website_sale: website_price includes pricelists/discounts
        website_price = (
            product.website_price
            if hasattr(product, 'website_price') else product.list_price
        )

        data = {}
        if 'id'                      in include: data['id']                      = product.id
        if 'name'                    in include: data['name']                    = product.name
        if 'description'             in include: data['description']             = product.description_sale or ''
        if 'price'                   in include: data['price']                   = product.list_price
        if 'website_price'           in include: data['website_price']           = website_price
        if 'currency'                in include: data['currency']                = product.currency_id.name if product.currency_id else 'PEN'
        if 'image_url'               in include: data['image_url']               = image_url
        if 'category_id'             in include: data['category_id']             = categ_id
        if 'category_name'           in include: data['category_name']           = categ_name
        if 'in_stock'                in include: data['in_stock']                = product.qty_available > 0 if hasattr(product, 'qty_available') else True
        if 'qty_available'           in include: data['qty_available']           = product.qty_available if hasattr(product, 'qty_available') else 0
        if 'active'                  in include: data['active']                  = product.active
        if 'is_published'            in include: data['is_published']            = product.is_published if hasattr(product, 'is_published') else True
        if 'website_description'     in include: data['website_description']     = product.website_description or '' if hasattr(product, 'website_description') else ''
        if 'seo_name'                in include: data['seo_name']                = product.website_slug if hasattr(product, 'website_slug') else None
        if 'website_meta_title'      in include: data['website_meta_title']      = product.website_meta_title or '' if hasattr(product, 'website_meta_title') else ''
        if 'website_meta_description'in include: data['website_meta_description']= product.website_meta_description or '' if hasattr(product, 'website_meta_description') else ''
        if 'ribbon'                  in include: data['ribbon']                  = product.website_ribbon_id.html if hasattr(product, 'website_ribbon_id') and product.website_ribbon_id else None
        return data

    def _category_to_dict(self, category):
        return {
            'id': category.id,
            'name': category.name,
            'slug': category.website_slug if hasattr(category, 'website_slug') else None,
            'parent_id': category.parent_id.id if category.parent_id else None,
            'child_ids': category.child_id.ids if hasattr(category, 'child_id') else [],
            'image_url': (
                f'/web/image/product.public.category/{category.id}/image_512'
                if hasattr(category, 'image_512') and category.image_512 else None
            ),
        }

    # ── CORS preflight ────────────────────────────────────────────────────────

    @http.route([
        '/api/shop/products',
        '/api/shop/product/<int:product_id>',
        '/api/shop/categories',
    ], auth='none', methods=['OPTIONS'], csrf=False)
    def options(self, **kwargs):
        return Response(status=204, headers=self._cors_headers())

    # ── GET /api/shop/products ─────────────────────────────────────────────────

    @http.route('/api/shop/products', auth='public', methods=['GET'], csrf=False)
    def get_products(self, **kwargs):
        """
        Query params:
          category_id  — filter by public category (int)
          search       — full-text search on name
          page         — page number (default 1)
          limit        — results per page (default 20, max 100)
          fields       — comma-separated list of fields to return (default: all)
                         e.g. ?fields=id,name,price,image_url,category_name,in_stock
        Only returns published products (is_published=True).
        """
        try:
            page = max(1, int(kwargs.get('page', 1)))
            limit = min(100, max(1, int(kwargs.get('limit', 20))))
            offset = (page - 1) * limit

            # Field projection
            fields_param = kwargs.get('fields', '').strip()
            if fields_param:
                requested = {f.strip() for f in fields_param.split(',') if f.strip()}
                fields = requested & self._PRODUCT_ALL_FIELDS or None
            else:
                fields = None

            # Base domain: only published products visible on website
            domain = [
                ('sale_ok', '=', True),
                ('active', '=', True),
                ('is_published', '=', True),
            ]

            # Filter by public category if provided
            category_id = kwargs.get('category_id')
            if category_id:
                domain.append(('public_categ_ids', 'child_of', int(category_id)))

            search_term = kwargs.get('search', '').strip()
            if search_term:
                domain.append(('name', 'ilike', search_term))

            ProductTemplate = request.env['product.template'].sudo()
            total = ProductTemplate.search_count(domain)
            products = ProductTemplate.search(domain, limit=limit, offset=offset)

            return self._json_response({
                'products': [self._product_to_dict(p, fields) for p in products],
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit,
            })
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    # ── GET /api/shop/product/<id> ─────────────────────────────────────────────

    @http.route('/api/shop/product/<int:product_id>', auth='public', methods=['GET'], csrf=False)
    def get_product(self, product_id, **kwargs):
        """Return full product detail including variants and extra images.
        Only returns the product if it is published (is_published=True).
        """
        try:
            product = request.env['product.template'].sudo().browse(product_id)
            if not product.exists() or not product.active:
                return self._json_response({'error': 'Product not found'}, status=404)
            if hasattr(product, 'is_published') and not product.is_published:
                return self._json_response({'error': 'Product not found'}, status=404)

            data = self._product_to_dict(product)

            # Extra images
            extra_images = []
            for img in product.product_template_image_ids:
                extra_images.append(
                    f'/web/image/product.image/{img.id}/image_1920'
                )
            data['extra_images'] = extra_images

            # Variants
            variants = []
            for variant in product.product_variant_ids:
                variant_data = {
                    'id': variant.id,
                    'name': variant.display_name,
                    'price': variant.lst_price,
                    'website_price': variant.website_price if hasattr(variant, 'website_price') else variant.lst_price,
                    'attributes': [],
                }
                for val in variant.product_template_attribute_value_ids:
                    variant_data['attributes'].append({
                        'attribute': val.attribute_id.name,
                        'value': val.name,
                    })
                variants.append(variant_data)
            data['variants'] = variants

            return self._json_response({'product': data})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    # ── GET /api/shop/categories ───────────────────────────────────────────────

    @http.route('/api/shop/categories', auth='public', methods=['GET'], csrf=False)
    def get_categories(self, **kwargs):
        """Return flat list of website public categories (product.public.category).
        Falls back to internal product.category if website_sale is not installed.
        """
        try:
            if 'product.public.category' in request.env:
                categories = request.env['product.public.category'].sudo().search([])
                return self._json_response({
                    'categories': [self._category_to_dict(c) for c in categories],
                })
            else:
                # Fallback: internal categories
                categories = request.env['product.category'].sudo().search([])
                return self._json_response({
                    'categories': [{
                        'id': c.id,
                        'name': c.name,
                        'slug': None,
                        'parent_id': c.parent_id.id if c.parent_id else None,
                        'child_ids': c.child_id.ids,
                        'image_url': None,
                    } for c in categories],
                })
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)
