# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    apiperu_url = fields.Char(string=u'URL apiperú', default='https://apiperu.dev/api')
    apiperu_token = fields.Char(string=u'Token apiperú')