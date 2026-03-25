# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveQueryStatusWizard(models.TransientModel):
    _name = 'account.move.query.status.wizard'
    _description = 'Consulta masiva de estado SUNAT'

    date_from = fields.Date(string='Fecha desde', required=True)
    date_to = fields.Date(string='Fecha hasta', required=True, default=fields.Date.today)

    def action_query_status(self):
        moves = self.env['account.move'].search([
            ('state', '!=', 'draft'),
            ('external_id', '!=', False),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
        ])

        if not moves:
            raise UserError(
                'No se encontraron facturas enviadas a SUNAT en el rango de fechas seleccionado.'
            )

        errors = []
        updated = 0
        for move in moves:
            try:
                move.action_invoice_query_status()
                updated += 1
            except Exception as e:
                errors.append(f'{move.name}: {str(e)}')

        msg = f'Se actualizó el estado de {updated} comprobante(s).'
        if errors:
            msg += f'\n\nErrores ({len(errors)}):\n' + '\n'.join(errors[:10])

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Consulta masiva completada',
                'message': msg,
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            },
        }
