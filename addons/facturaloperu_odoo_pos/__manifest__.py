{
    'name': "FacturaloPeru Punto de Venta",
    'category': "web",
    'version': "19.0.1.0.0",
    "author": "FacturaloPeru",
    'website': "www.facturaloperu.com",
    'summary': "Módulo que se integra con POS",

    'depends': [
        'base',
        'point_of_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/api_url.xml',
        'data/pos_order_document_type.xml',
        'data/journal.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/pos_order_sync_view.xml',
        'views/pos_order_document_type_view.xml',
        'views/pos_order_serial_number_view.xml',
        'views/account_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'facturaloperu_odoo_pos/static/src/css/api_frame.css',
        ],
        'point_of_sale._assets_pos': [
            'facturaloperu_odoo_pos/static/src/libs/noty/noty.min.js',
            'facturaloperu_odoo_pos/static/src/css/pos.css',
            'facturaloperu_odoo_pos/static/src/libs/noty/noty.css',
            'facturaloperu_odoo_pos/static/src/libs/noty/themes/bootstrap-v4.css',
        ],
    },
    'license': 'AGPL-3',
    'auto_install': False,
    'installable': True,
    'application': True,
    "sequence": 1,
}
