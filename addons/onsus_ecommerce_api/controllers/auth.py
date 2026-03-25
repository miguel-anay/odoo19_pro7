import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessDenied


class AuthController(http.Controller):

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

    @http.route(['/api/auth/login', '/api/auth/logout', '/api/auth/me'],
                auth='none', methods=['OPTIONS'], csrf=False)
    def options(self, **kwargs):
        return Response(status=204, headers=self._cors_headers())

    @http.route('/api/auth/login', auth='none', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        """
        Body JSON: { "login": "user@email.com", "password": "secret", "db": "mydb" }
        Returns: { "uid": 1, "name": "...", "email": "..." }
        """
        try:
            body = json.loads(request.httprequest.data or '{}')
            login = body.get('login', '').strip()
            password = body.get('password', '')
            db = body.get('db') or request.db

            if not login or not password:
                return self._json_response({'error': 'login and password required'}, status=400)

            uid = request.session.authenticate(db, login, password)
            if not uid:
                return self._json_response({'error': 'Invalid credentials'}, status=401)

            user = request.env['res.users'].sudo().browse(uid)
            return self._json_response({
                'uid': uid,
                'name': user.name,
                'email': user.email or login,
                'session_id': request.session.sid,
            })
        except AccessDenied:
            return self._json_response({'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/auth/logout', auth='user', methods=['POST'], csrf=False)
    def logout(self, **kwargs):
        try:
            request.session.logout(keep_db=True)
            return self._json_response({'success': True})
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/auth/me', auth='user', methods=['GET'], csrf=False)
    def me(self, **kwargs):
        try:
            user = request.env.user
            return self._json_response({
                'uid': user.id,
                'name': user.name,
                'email': user.email or '',
                'partner_id': user.partner_id.id,
            })
        except Exception as e:
            return self._json_response({'error': str(e)}, status=500)
