# -*- coding: utf-8 -*-
{
    'name': "Catalogos y Tablas SUNAT",
    'summary': """
        Tablas y Catalogos segun SUNAT para facturacion electronica
    """,
    'description': """
        Catalogos y Tablas SUNAT - Odoo 19
        ==================================

        Tablas y catalogos requeridos por SUNAT para:
        - Facturacion electronica
        - Guias de remision
        - Libros electronicos
    """,
    'author': "FacturaloPeru",
    'website': "www.facturaloperu.com",
    'category': 'Accounting/Localizations',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_pe_datas.xml',
        'data/l10n_pe_datas.xml',
        'data/l10n_pe.datas.csv'
    ],
    'installable': True,
    'auto_install': False,
}
