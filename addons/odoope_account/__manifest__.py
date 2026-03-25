# -*- coding: utf-8 -*-
{
    'name': "Base contable Peru",
    'summary': """
        Base contable para localizacion peruana
    """,
    'description': """
        Modulo base contable para Peru - Odoo 19
        ========================================

        Extiende la funcionalidad contable para cumplir con
        los requerimientos de la normativa peruana.
    """,
    'author': "FacturaloPeru",
    'website': "www.facturaloperu.com",
    'category': 'Accounting/Localizations',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_pe_sunat_data',
        'odoope_currency',
        'odoope_product'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account.xml',
    ],
    'installable': True,
    'auto_install': False,
}
