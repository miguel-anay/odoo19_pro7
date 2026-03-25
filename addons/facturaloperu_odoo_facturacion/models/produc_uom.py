# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductUom(models.Model):
    _inherit = 'uom.uom'

    code = fields.Char(
        string='Código Sunat',
        compute='_compute_code'
    )

    l10n_pe_uom_code_id = fields.Many2one(
        comodel_name='l10n_pe.datas',
        domain=[('table_code', '=', 'PE.CPE.CATALOG3')],
        string='Unidad de medida Sunat',
        help='Confirmar unidad de medida según catálogo Sunat'
    )

    @api.depends('l10n_pe_uom_code_id')
    def _compute_code(self):
        for rec in self:
            if rec.l10n_pe_uom_code_id.code:
                rec.code = rec.l10n_pe_uom_code_id.code
            else:
                rec.code = False
