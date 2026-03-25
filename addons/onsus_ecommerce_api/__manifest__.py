{
    'name': 'Onsus eCommerce API',
    'version': '19.0.1.0.0',
    'summary': 'REST JSON API for onsus-nextjs eCommerce frontend',
    'description': """
        Exposes product, category, cart, wishlist, and auth endpoints
        for consumption by the onsus-nextjs Next.js frontend.
    """,
    'author': 'Onsus',
    'category': 'eCommerce',
    'depends': ['product', 'sale', 'stock'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
