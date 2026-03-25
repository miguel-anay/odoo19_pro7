# -*- coding: utf-8 -*-
{
    'name': 'Contactos - Consulta API: RUC DNI',
    'version': '19.0.1.0.0',
    'author': 'FacturaloPeru',
    'category': 'Sales/CRM',
    'summary': 'Consulta de datos DNI y RUC via API',
    'license': 'LGPL-3',
    'description': """
        Consulta DNI/RUC - Odoo 19
        ==========================

        Permite consultar datos de DNI y RUC desde
        el formulario de contactos via API.
    """,
    'website': 'www.facturaloperu.com',
    'depends': ['base', 'contacts', 'odoope_einvoice_base'],
    'data': [
        'views/res_company.xml',
        'views/res_partner_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'l10n_pe_partner_consulta_dni_ruc/static/src/xml/consulta_ruc_widget.xml',
            'l10n_pe_partner_consulta_dni_ruc/static/src/js/consulta_ruc_widget.js',
        ],
        'point_of_sale._assets_pos': [
            'l10n_pe_partner_consulta_dni_ruc/static/src/xml/consulta_ruc_widget.xml',
            'l10n_pe_partner_consulta_dni_ruc/static/src/js/consulta_ruc_widget.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
}