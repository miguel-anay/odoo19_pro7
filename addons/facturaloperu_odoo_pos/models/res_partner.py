from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    doc_number = fields.Char(
        string='Document Number',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            doc_number = vals.get('doc_number', False)
            vat = vals.get('vat', False)
            if doc_number:
                vals['vat'] = doc_number
            if vat:
                vals['doc_number'] = vat
        return super().create(vals_list)

    def write(self, vals):
        doc_number = vals.get('doc_number', False)
        vat = vals.get('vat', False)
        if doc_number:
            vals['vat'] = doc_number
        if vat:
            vals['doc_number'] = vat
        return super().write(vals)
