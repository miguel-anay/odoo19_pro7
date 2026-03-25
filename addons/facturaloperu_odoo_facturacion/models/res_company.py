# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    api_url = fields.Char('URL', help="URL base del Facturador PRO (ej. https://mi-empresa.qhipa.org.pe)")
    api_token = fields.Char('API Token', help="Token Bearer obtenido desde el panel del Facturador PRO")
    api_send_email = fields.Boolean('Envío de email', help="Envío de comprobante electrónico al email de cliente", default=False)