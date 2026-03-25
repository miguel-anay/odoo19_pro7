# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    province_id = fields.Many2one('res.country.state', 'Provincia')
    district_id = fields.Many2one('res.country.state', 'Distrito')

    @api.model
    def _address_fields(self):
        address_fields = super()._address_fields()
        address_fields.extend(['province_id', 'district_id'])
        return address_fields

    @api.onchange('district_id')
    def onchange_district(self):
        if self.district_id:
            pass
