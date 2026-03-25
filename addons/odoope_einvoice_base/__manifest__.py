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
    'name': 'Factura Electronica - Base',
    'version': '19.0.1.0.0',
    'author': 'FacturaloPeru, Odoo Peru',
    'category': 'Accounting/Localizations',
    'summary': 'Tablas y requisitos minimos para la factura electronica SUNAT',
    'license': 'LGPL-3',
    'contributors': [
        'Leonidas Pezo <leonidas@odooperu.pe>',
    ],
    'description': """
Factura Electronica - Base - Odoo 19
====================================

Tablas:
-------
    * Tablas requeridas por la Factura electronica
    * Catalogos SUNAT para facturacion electronica
    * Tipos de documentos, operaciones, afectaciones IGV

Compatible con Odoo 19 y la normativa peruana vigente.
    """,
    'website': 'www.facturaloperu.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/einvoice_view.xml',
        'data/einvoice_data.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
