# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    def _get_default_pdf_report_id(self, move):
        """Usa el reporte SUNAT para facturas/boletas electrónicas PE."""
        if move.journal_id.l10n_pe_document_type_id:
            return self.env.ref('facturaloperu_odoo_facturacion.reporte_account_invoice_sunat')
        return super()._get_default_pdf_report_id(move)
