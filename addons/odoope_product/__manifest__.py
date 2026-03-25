# -*- coding: utf-8 -*-
{
    'name': "Producto Peru",
    'summary': """
        Control de productos Peru para facturacion electronica
    """,
    'description': """
        Producto Peru - Odoo 19
        =======================

        Control de productos para cumplir con los
        requerimientos de SUNAT en facturacion electronica.
    """,
    'author': "FacturaloPeru",
    'website': "www.facturaloperu.com",
    'category': 'Inventory/Inventory',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'l10n_pe_sunat_data',
    ],
    'data': [
        'views/product.xml',
    ],
    'installable': True,
    'auto_install': False,
}
