# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    l10n_pe_debit_note_code = fields.Selection(selection="_get_l10n_pe_debit_note_type", string="Codigo de nota de débito")
    l10n_pe_credit_note_code = fields.Selection(selection="_get_l10n_pe_credit_note_type", string="Codigo de nota de credito")

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMoveReversal, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            move_obj = self.env['account.move'].browse(active_id)
            if move_obj.journal_id.l10n_pe_document_type_id \
                    and not (move_obj.journal_id.l10n_pe_journal_debit_id and move_obj.journal_id.l10n_pe_journal_credit_id):
                raise UserError('Configure diario de NC y ND en diario: {}'.format(move_obj.journal_id.name))
        return res

    @api.model
    def _get_l10n_pe_credit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.model
    def _get_l10n_pe_debit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG10")

    def reverse_moves(self, is_modify=False):
        return super(AccountMoveReversal, self).reverse_moves()
