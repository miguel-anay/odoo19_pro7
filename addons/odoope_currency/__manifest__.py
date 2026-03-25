# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009-TODAY Odoo Peru(<http://www.odooperu.pe>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Tipo de Cambio Peru',
    'version': '19.0.1.0.0',
    'author': 'FacturaloPeru, Odoo Peru',
    'category': 'Accounting/Localizations',
    'summary': 'Permite ingresar tipo de cambio en formato peruano.',
    'license': 'LGPL-3',
    'contributors': [
        'Leonidas Pezo <leonidas@odooperu.pe>',
    ],
    'description': """
Tipo de Cambio Peru - Odoo 19
=============================

Registra el tipo de cambio al estilo peruano:

ANTES:
 S/. 1 = S/. 1
   $ 1 = S/. 0.30769

AHORA:
 S/. 1 = S/. 1
   $ 1 = S/. 3.25

Compatible con Odoo 19 y la normativa peruana vigente.
    """,
    'website': 'www.facturaloperu.com',
    'depends': ['account'],
    'data': [
        'views/res_currency_view.xml',
        'data/res_currency_data.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 2,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
