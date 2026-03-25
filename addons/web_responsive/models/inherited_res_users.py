# Copyright 2018 Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    SELF_WRITEABLE_FIELDS = ['chatter_position']
    SELF_READABLE_FIELDS = ['chatter_position']

    chatter_position = fields.Selection([
        ('normal', 'Normal'),
        ('sided', 'Sided'),
    ], string="Chatter Position", default='normal')
