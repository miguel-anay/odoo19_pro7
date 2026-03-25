# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Niyas Raphy(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Company Logo In POS Receipt',
    'summary': """Add Company Logo, Info & Customer name to POS Ticket""",
    'version': '19.0.1.0.0',
    'description': """Add Company Logo, Info & Customer name to POS Ticket""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': 'Sales/Point of Sale',
    'depends': ['base', 'point_of_sale'],
    'license': 'LGPL-3',
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_ticket/static/src/xml/pos_ticket_view.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
