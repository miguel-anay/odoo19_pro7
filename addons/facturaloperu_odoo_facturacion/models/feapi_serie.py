# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FeapiSerie(models.Model):
    _name = 'feapi.serie'
    _description = 'Serie de Facturación'

    name = fields.Char('Serie', size=4, required=True)
    description = fields.Char('Descripcion')

    invoice_id = fields.One2many("account.move", "serie_id")

    document_type_id = fields.Many2one("einvoice.catalog.01", string="Tipo de Documento")

    last_number_feapi = fields.Char(
        string='Último número emitido',
        compute='_compute_last_number_feapi',
    )
    total_invoices = fields.Integer(
        string='Total emitidos',
        compute='_compute_last_number_feapi',
    )

    @api.depends('name')
    def _compute_last_number_feapi(self):
        for serie in self:
            last = self.env['account.move'].search([
                ('journal_id.code', '=', serie.name),
                ('number_feapi', '!=', False),
                ('state', '=', 'posted'),
            ], order='id desc', limit=1)
            serie.last_number_feapi = last.number_feapi if last else '—'
            serie.total_invoices = self.env['account.move'].search_count([
                ('journal_id.code', '=', serie.name),
                ('number_feapi', '!=', False),
                ('state', '=', 'posted'),
            ])

class FeapiDocumentType(models.Model):
    _inherit = 'einvoice.catalog.01'

    serie_id = fields.One2many("feapi.serie", "document_type_id")
