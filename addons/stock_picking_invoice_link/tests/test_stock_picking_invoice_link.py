# Copyright 2016 Oihane Crucelaegui - AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class TestStockPickingInvoiceLink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.product_storable = cls.env['product.product'].create({
            'name': 'Test Storable Product',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100.0,
        })
        cls.product_service = cls.env['product.product'].create({
            'name': 'Test Service Product',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 50.0,
        })
        # Update stock quantity
        cls.env['stock.quant']._update_available_quantity(
            cls.product_storable,
            cls.env.ref('stock.stock_location_stock'),
            100.0
        )

    def test_sale_stock_invoice_link(self):
        """Test that invoices are linked to pickings."""
        # Create sale order
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_storable.name,
                    'product_id': self.product_storable.id,
                    'product_uom_qty': 2,
                    'product_uom': self.product_storable.uom_id.id,
                    'price_unit': self.product_storable.list_price,
                }),
                (0, 0, {
                    'name': self.product_service.name,
                    'product_id': self.product_service.id,
                    'product_uom_qty': 2,
                    'product_uom': self.product_service.uom_id.id,
                    'price_unit': self.product_service.list_price,
                }),
            ],
        })
        so.action_confirm()

        self.assertTrue(
            so.picking_ids,
            'Sale Stock: no picking created for storable products'
        )

        # Deliver the products
        picking = so.picking_ids[0]
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

        self.assertEqual(picking.state, 'done', 'Picking should be done')

        # Create invoice
        invoices = so._create_invoices()

        self.assertTrue(invoices, 'Invoice should be created')

        # Check links between invoice and picking
        invoice = invoices[0]
        self.assertIn(
            picking,
            invoice.picking_ids,
            'Invoice should be linked to the picking'
        )

    def test_picking_view_invoice(self):
        """Test the action to view invoices from picking."""
        # Create sale order
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_storable.name,
                    'product_id': self.product_storable.id,
                    'product_uom_qty': 1,
                    'product_uom': self.product_storable.uom_id.id,
                    'price_unit': self.product_storable.list_price,
                }),
            ],
        })
        so.action_confirm()

        # Deliver
        picking = so.picking_ids[0]
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

        # Create invoice
        invoices = so._create_invoices()
        invoice = invoices[0]

        # Test action view invoice (single invoice)
        result = picking.action_view_invoice()
        self.assertEqual(result['res_id'], invoice.id)
