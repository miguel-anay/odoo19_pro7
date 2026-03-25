# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTax(models.Model):
    _inherit = 'account.tax'

    code_affectation = fields.Char(
        string='Tipo segun sunat',
        compute='_compute_code_affectation',
        default='10'
    )

    @api.depends('l10n_pe_tax_type_id')
    def _compute_code_affectation(self):
        for rec in self:
            if rec.l10n_pe_tax_type_id.name:
                name = rec.l10n_pe_tax_type_id.name
                if name == 'INA':
                    rec.code_affectation = 30
                elif name == 'GRA':
                    rec.code_affectation = 16
                elif name == 'EXO':
                    rec.code_affectation = 20
                elif name == 'IGV':
                    rec.code_affectation = 10
                elif name == 'ISC':
                    rec.code_affectation = 10
                elif name == 'ICBPER':
                    rec.code_affectation = 10
                else:
                    rec.code_affectation = 10
            else:
                rec.code_affectation = 10
