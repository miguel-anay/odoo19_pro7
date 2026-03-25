from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    ticket_html = fields.Html(string='Ticket html')
