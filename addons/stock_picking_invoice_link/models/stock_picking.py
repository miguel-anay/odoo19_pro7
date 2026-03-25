# Copyright 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2015-2016 AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_ids = fields.Many2many(
        comodel_name='account.move',
        copy=False,
        string='Invoices',
        readonly=True,
    )

    def action_view_invoice(self):
        """This function returns an action that display existing invoices
        of given stock pickings.
        It can either be a in a list or in a form view, if there is only
        one invoice to show.
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('account.action_move_out_invoice_type')
        if len(self.invoice_ids) > 1:
            action['domain'] = [('id', 'in', self.invoice_ids.ids)]
        else:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = self.invoice_ids.id
        return action
