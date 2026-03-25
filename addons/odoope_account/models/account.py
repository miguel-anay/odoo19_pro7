# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_pe_exchange_rate = fields.Float(
        string='Tipo de cambio',
        compute='_compute_l10n_pe_exchange_rate',
        digits=(10, 3)
    )
    l10n_pe_invoice_origin_id = fields.Many2one(
        comodel_name='account.move',
        string='Documento rectificado',
        readonly=True
    )

    @api.depends('invoice_date', 'currency_id')
    def _compute_l10n_pe_exchange_rate(self):
        today = fields.Date.context_today(self)
        for move in self:
            date = (move.l10n_pe_invoice_origin_id or move).invoice_date or today
            move.l10n_pe_exchange_rate = move.currency_id.with_context(date=date).rate_pe or 1.0

    def _get_currency_rate_date(self):
        self.ensure_one()
        return self.l10n_pe_invoice_origin_id.invoice_date or self.date or self.invoice_date


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_pe_tax_type_id = fields.Many2one(
        comodel_name='l10n_pe.datas',
        domain=[('table_code', '=', 'PE.CPE.CATALOG5')],
        string='Tipo segun SUNAT'
    )
