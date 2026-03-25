import pytz
from datetime import datetime
from odoo import api, models

class InvoiceReportSunat(models.AbstractModel):
    _name = "report.facturaloperu_odoo_facturacion.report_mov_template"
    _description = "Invoice Report SUNAT"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        tz = pytz.timezone(self.env.user.tz or 'America/Lima')
        emission_times = {}
        for doc in docs:
            dt_utc = doc.create_date or datetime.utcnow()
            dt_local = pytz.utc.localize(dt_utc).astimezone(tz)
            emission_times[doc.id] = dt_local.strftime('%H:%M:%S')
        return {
            "doc_ids": docids,
            "docs": docs,
            "emission_times": emission_times,
        }
