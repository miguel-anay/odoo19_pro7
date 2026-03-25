# -*- coding: utf-8 -*-

import re
import requests

from bs4 import BeautifulSoup
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

SUNAT = 'sunat'
PURCHASE = 'purchase'
SALE = 'sale'

SOURCE_RATE = [
    (SUNAT, 'Sunat')
]

TYPES = [
    (PURCHASE, 'Compra'),
    (SALE, 'Venta')
]


class Currency(models.Model):
    _inherit = "res.currency"

    rate_pe = fields.Float(
        compute='_compute_current_rate_pe',
        string='Cambio del dia',
        digits=(12, 4),
        help='Tipo de cambio del dia en formato peruano.'
    )
    type = fields.Selection(TYPES, string='Tipo', default='sale')
    l10n_pe_source_rate = fields.Selection(selection=SOURCE_RATE, string='Origen del TC')

    _sql_constraints = [
        ('rounding_gt_zero', 'CHECK (rounding>0)', 'The rounding factor must be greater than 0!')
    ]

    def _compute_current_rate_pe(self):
        date = self._context.get('date') or fields.Date.today()
        company_id = self._context.get('company_id') or self.env.company.id
        query = """SELECT c.id, (SELECT r.rate_pe FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1) AS rate_pe
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self.env.cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_rates = dict(self.env.cr.fetchall())
        for currency in self:
            currency.rate_pe = currency_rates.get(currency.id) or 1.0

    @api.depends('name', 'type')
    def _compute_display_name(self):
        for currency in self:
            type_label = dict(TYPES).get(currency.type, '')
            currency.display_name = f"{currency.name} - {type_label}" if type_label else currency.name

    @api.model
    def l10n_pe_get_currency(self):
        currencies = self.search([('l10n_pe_source_rate', '!=', False)])
        for currency in currencies:
            if currency.l10n_pe_source_rate == SUNAT:
                currency._l10n_pe_from_sunat()

    def l10n_pe_is_company_currency(self):
        self.ensure_one()
        return self == self.env.company.currency_id

    def _l10n_pe_from_sunat(self):
        self.ensure_one()
        try:
            r = requests.get("http://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias", timeout=10)
            soup = BeautifulSoup(r.text, "lxml")
            index = -1 if self.type == SALE else -2
            res = soup.find_all("td", {"align": "center", "class": "tne10"})[index]
            value = re.sub(r"[\r\n\t]", "", res.text)
            if self and value and value.strip() and self.name in ['USD']:
                obj_currency_rate = self.rate_ids.filtered(
                    lambda x: x.name.strftime('%Y-%m-%d') == fields.Date.today().strftime('%Y-%m-%d')
                )
                if not obj_currency_rate:
                    self.env['res.currency.rate'].create({
                        'name': fields.Date.today(),
                        'rate_pe': float(value.strip()),
                        'currency_id': self.id,
                        'rate': 1 / float(value.strip())
                    })
        except Exception:
            pass

    def l10n_pe_get_rate_by_date(self, date):
        self.ensure_one()
        if self != self.env.company.currency_id and date:
            rate_obj = self.env['res.currency.rate'].search(
                [('currency_id', '=', self.id), ('name', '<=', date)],
                order='name DESC',
                limit=1
            )
            if rate_obj:
                return rate_obj.rate_pe
            elif self:
                raise ValidationError(_('Configure un tipo de cambio para moneda {} con fecha {}').format(self.name, date))
        else:
            return 1


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    rate_pe = fields.Float(
        string='Cambio',
        digits=(12, 4),
        help='Tipo de cambio en formato peruano. Ejm: 3.25 si $1 = S/. 3.25'
    )
    type = fields.Selection(related="currency_id.type", store=True)

    @api.onchange('rate_pe')
    def onchange_rate_pe(self):
        if self.rate_pe > 0:
            self.rate = 1 / self.rate_pe
