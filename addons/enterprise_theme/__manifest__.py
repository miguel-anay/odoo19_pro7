# -*- coding: utf-8 -*-
# Copyright 2016, 2017 Openworx
# Copyright 2017 Hugo Rodrigues
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
# pylint: disable=pointless-statement
# pylint: disable=missing-docstring

{
    "name": "Enterprise Backend Theme",
    "summary": "Enterprise feel on Odoo Community",
    "version": "19.0.1.0.0",
    "category": "Themes/Backend",
    "website": "https://hugorodrigues.net",
    "author": "Openworx, Hugo Rodrigues",
    "license": "LGPL-3",
    "installable": True,
    "images": [
        "static/description/dashboard.png"
    ],
    "depends": [
        'web',
    ],
    "assets": {
        "web.assets_backend": [
            "enterprise_theme/static/src/less/drawer.less",
            "enterprise_theme/static/src/less/variables.less",
            "enterprise_theme/static/src/less/bootswatch.less",
            "enterprise_theme/static/src/less/style.less",
        ],
    },
    "data": [
        'views/res_company_view.xml',
        'views/res_users_view.xml',
    ],
}
