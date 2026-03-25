# Copyright 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Override to link pickings to invoices when creating from SO."""
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        for move in moves:
            # Get all pickings related to the sale orders being invoiced
            sale_orders = move.line_ids.sale_line_ids.order_id
            pickings = sale_orders.picking_ids.filtered(
                lambda p: p.state == 'done'
            )
            if pickings:
                move.picking_ids = [(6, 0, pickings.ids)]
        return moves


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        """Override to link stock moves to invoice lines."""
        vals = super()._prepare_invoice_line(**optional_values)
        # Get done moves that haven't been invoiced yet
        move_ids = self.move_ids.filtered(
            lambda x: x.state == 'done' and
            not x.invoice_line_id and
            not x.location_dest_id.scrap_location and
            x.location_dest_id.usage == 'customer'
        ).ids
        if move_ids:
            vals['move_line_ids'] = [(6, 0, move_ids)]
        return vals
