from odoo import (
    api,
    fields,
    models
)
import requests


class PosConfig(models.Model):
    _inherit = 'pos.config'

    is_facturalo_api = fields.Boolean(
        string='Facturalo Peru API'
    )
    iface_facturalo_url_endpoint = fields.Char(
        string='Endpoint url for Facturalo API'
    )
    iface_facturalo_token = fields.Char(
        string='Token for Facturalo API'
    )
    facturalo_endpoint_state = fields.Selection(
        [('draft', 'Draft'), ('success', 'Success'), ('error', 'Error')],
        string='Is the URL endpoint valid?',
        default='draft'
    )

    print_pdf = fields.Boolean(
        string="Imprimir PDF enviado a Facturación",
        default=False
    )

    l10n_pe_pos_auto_invoice = fields.Boolean(
        string='POS auto factura',
        default=1
    )
    l10n_pe_invoice_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='pos_config_invoice_journal_rel',
        column1='config_id',
        column2='journal_id',
        string='Diarios CPE',
        domain=[('type', '=', 'sale')],
        help="Diarios contables para la creación de comprobantes"
    )
    l10n_pe_currency_ids = fields.Many2many(
        comodel_name='res.currency',
        string='Monedas CPE',
    )

    iface_api_send_email = fields.Boolean(
        string='Envío de email',
        help='Envío de comprobante electrónico al email de cliente',
        default=False
    )

    @api.onchange('iface_facturalo_url_endpoint', 'iface_facturalo_token')
    def set_valid_endpoint(self):
        self.facturalo_endpoint_state = 'draft'

    def test_facturalo_api_connection(self):
        self.ensure_one()
        headers = {'Authorization': 'Bearer ' + self.iface_facturalo_token}

        r = requests.post(
            self.iface_facturalo_url_endpoint,
            data={},
            headers=headers
        )
        if r.status_code == 404:
            self.facturalo_endpoint_state = 'error'
        else:
            self.facturalo_endpoint_state = 'success'
