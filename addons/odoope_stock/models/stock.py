# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_pe_type_operation_id = fields.Many2one(
        comodel_name='l10n_pe.datas',
        domain=[('table_code', 'in', ['PE.TABLA12'])],
        string='Tipo de operación'
    )
    l10n_pe_number = fields.Char(string='Correlativo')


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    l10n_pe_type_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string="Secuencia PE"
    )
