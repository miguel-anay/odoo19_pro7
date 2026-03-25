# -*- coding: utf-8 -*-
{
    'name': "Stock Peru",
    'summary': """
        Control de inventario Peru
    """,
    'description': """
        Stock Peru - Odoo 19
        ====================

        Control de inventario para cumplir con los
        requerimientos de SUNAT.
    """,
    'author': "FacturaloPeru",
    'website': "www.facturaloperu.com",
    'category': 'Inventory/Inventory',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'odoope_product',
        'l10n_pe_sunat_data',
    ],
    'data': [
        'views/stock.xml',
    ],
    'installable': True,
    'auto_install': False,
}
