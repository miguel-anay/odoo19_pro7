# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CountryState(models.Model):
    _inherit = 'res.country.state'
    _description = "Country state"

    code = fields.Char('Country Code', size=9,
            help='The ISO country code in two chars.\n'
            'You can use this field for quick search.')
    state_id = fields.Many2one('res.country.state', 'Departamento')
    province_id = fields.Many2one('res.country.state', 'Provincia')
