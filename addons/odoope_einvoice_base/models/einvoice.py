# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EinvoiceCatalog01(models.Model):
    _name = "einvoice.catalog.01"
    _description = 'Codigo de Tipo de documento'
    _rec_name = 'display_name'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            code = record.code or ''
            name = record.name or ''
            record.display_name = f"{code} - {name}" if code else name


class EinvoiceCatalog06(models.Model):
    _name = "einvoice.catalog.06"
    _description = 'Tipo de documento de Identidad'
    _rec_name = 'display_name'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    default = fields.Char(string='Valor por defecto', size=128)
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            code = record.code or ''
            name = record.name or ''
            record.display_name = f"{code} - {name}" if code else name


class EinvoiceCatalog07(models.Model):
    _name = "einvoice.catalog.07"
    _description = 'Codigos de Tipo de Afectacion del IGV'
    _rec_name = 'display_name'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    no_onerosa = fields.Boolean(string='No onerosa')
    type = fields.Selection([
        ('gravado', 'Gravado'),
        ('exonerado', 'Exonerado'),
        ('inafecto', 'Inafecto')
    ], string='Tipo')
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            code = record.code or ''
            name = record.name or ''
            record.display_name = f"{code} - {name}" if code else name


class EinvoiceCatalog08(models.Model):
    _name = "einvoice.catalog.08"
    _description = 'Codigos de Sistema de Calculo del ISC'
    _rec_name = 'display_name'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            code = record.code or ''
            name = record.name or ''
            record.display_name = f"{code} - {name}" if code else name


class EinvoiceCatalog09(models.Model):
    _name = "einvoice.catalog.09"
    _description = 'Codigos de Tipo de Nota de Credito Electronica'
    _rec_name = 'display_name'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            code = record.code or ''
            name = record.name or ''
            record.display_name = f"{code} - {name}" if code else name


class EinvoiceCatalog10(models.Model):
    _name = "einvoice.catalog.10"
    _description = 'Codigos de Tipo de Nota de Debito Electronica'
    _rec_name = 'display_name'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            code = record.code or ''
            name = record.name or ''
            record.display_name = f"{code} - {name}" if code else name


class EinvoiceCatalog16(models.Model):
    _name = "einvoice.catalog.16"
    _description = 'Codigos - Tipo de Precio de Venta Unitario'
    _rec_name = 'display_name'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            code = record.code or ''
            name = record.name or ''
            record.display_name = f"{code} - {name}" if code else name
