from odoo import api, fields, models
from odoo.exceptions import UserError
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
import json


class AccountMove(models.Model):
    _inherit = "account.move"

    picking_ids = fields.Many2many(comodel_name='stock.picking', string='Related Pickings', readonly=False, copy=False,
                                   help="Related pickings (only when the invoice has been generated from a sale order).")
    enable_voided_document = fields.Boolean(compute='_compute_enable_void_document')
    ticket_voided_document = fields.Char(string='Ticket de anulación', readonly=True, copy=False)
    link_voided_document = fields.Char(string='CDR Anulación', readonly=True, copy=False)
    reason_voided = fields.Char(string=u'Motivo de anulación', copy=False)
    l10n_pe_debit_note_code = fields.Selection(selection="_get_l10n_pe_debit_note_type", string="Codigo de nota de debito", readonly=True)
    l10n_pe_credit_note_code = fields.Selection(selection="_get_l10n_pe_credit_note_type", string="Codigo de nota de credito", readonly=True)
    l10n_pe_document_code = fields.Char(related='journal_id.l10n_pe_document_type_id.code')
    l10n_pe_hide_refund = fields.Boolean(compute='_compute_l10n_pe_hide_refund')

    @api.depends('l10n_pe_document_code', 'move_type', 'state', 'state_api')
    def _compute_l10n_pe_hide_refund(self):
        for record in self:
            record.l10n_pe_hide_refund = (
                record.l10n_pe_document_code in ['07', '08'] or
                record.move_type == 'out_refund' or
                record.state != 'posted' or
                record.state_api in ('null', 'nullable')
            )

    @api.model
    def _get_l10n_pe_credit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.model
    def _get_l10n_pe_debit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG10")

    @api.depends('invoice_date', 'number_feapi')
    def _compute_enable_void_document(self):
        today = fields.Date.context_today(self)
        for record in self:
            enable = False
            if record.number_feapi and record.number_feapi[0] in ['F', 'B'] and record.external_id:
                if record.invoice_date and (today - record.invoice_date).days < 7 and not record.ticket_voided_document:
                    enable = True
            record.enable_voided_document = enable

    def void_document(self):
        if not self.filtered(lambda record: record.reason_voided):
            raise UserError('Ingrese motivo de anulación en pestaña Otra información')

        data = {
            'fecha_de_emision_de_documentos': str(self.invoice_date) if self.invoice_date else '',
            'documentos': self.mapped(lambda record: {
                'external_id': record.external_id,
                'motivo_anulacion': record.reason_voided
            })
        }

        service = '/voided'
        if self.name[0] == 'B':
            data.update({'codigo_tipo_proceso': '3'})
            service = '/summaries'
        url = '{}{}'.format(self.company_id.api_url, service)
        response = self.send_request(url, data)
        if response and response['data']['ticket']:
            self.write({'ticket_voided_document': response['data']['ticket']})
            data = {
                "external_id": response['data']['external_id'],
                "ticket": response['data']['ticket']
            }
            url = '{}{}{}'.format(self.company_id.api_url, service, '/status')
            response = self.send_request(url, data)
            if response and response['links']['xml']:
                self.button_draft()
                self.write({
                    'link_voided_document': response['links']['xml'],
                    'state_api': 'null'
                })

    def send_request(self, url, data):
        token = self.company_id.api_token
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
        try:
            r = requests.post(url, data=json.dumps(data), headers=headers, timeout=15)
            response = r.json()
        except (ConnectionError, HTTPError) as e:
            raise UserError('Error Http')
        except (ConnectionError, Timeout) as e:
            raise UserError('El tiempo de envío se ha agotado, el servidor de la Sunat puede encontrarse no disponible temporalemente')

        if not response['success']:
            raise UserError(response['message'])
        return response

    def action_print_invoice_sunat(self):
        """Imprime el reporte de factura SUNAT"""
        self.ensure_one()
        return self.env.ref('facturaloperu_odoo_facturacion.reporte_account_invoice_a4').report_action(self)

    def action_print_invoice_ticket(self):
        """Imprime el reporte de factura en formato ticket 80mm"""
        self.ensure_one()
        return self.env.ref('facturaloperu_odoo_facturacion.reporte_account_invoice_ticket').report_action(self)



class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_pe_document_type_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', 'in', ['PE.CPE.CATALOG1'])],
                                               string='Tipo de documento')
    l10n_pe_journal_debit_id = fields.Many2one(comodel_name='account.journal', string='Nota de debito',
                                               domain=[('l10n_pe_document_type_id.code', 'in', ['08'])])
    l10n_pe_journal_credit_id = fields.Many2one(comodel_name='account.journal', string='Nota de credito',
                                                domain=[('l10n_pe_document_type_id.code', 'in', ['07'])])
    l10n_pe_sunat_code = fields.Char(string='Codigo sunat', related='l10n_pe_document_type_id.code')
    l10n_pe_send_sunat = fields.Boolean(string='Enviar a sunat')
