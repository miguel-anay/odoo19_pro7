# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

import requests


def get_data_doc_number(tipo_doc, numero_doc, format='json'):
    user, password = 'demorest', 'demo1234'
    url = 'http://py-devs.com/api'
    url = '%s/%s/%s' % (url, tipo_doc, str(numero_doc))
    res = {'error': True, 'message': None, 'data': {}}
    try:
        response = requests.get(url, auth=(user, password), timeout=10)
    except requests.exceptions.ConnectionError:
        res['message'] = 'Error en la conexion'
        return res

    if response.status_code == 200:
        res['error'] = False
        res['data'] = response.json()
    else:
        try:
            res['message'] = response.json()['detail']
        except Exception:
            res['error'] = True
    return res


class ResPartner(models.Model):
    _inherit = 'res.partner'

    registration_name = fields.Char('Name', size=128, index=True)
    state = fields.Selection([
        ('habido', 'Habido'),
        ('nhabido', 'No Habido')
    ], 'State')
    ubigeo = fields.Char(string='Ubigeo', size=6)

    @api.model
    def _default_catalog(self):
        # Default: DNI para Persona (is_company=False es el default de nuevos contactos)
        return self.env["einvoice.catalog.06"].search([('code', '=', '1')], limit=1)

    catalog_06_id = fields.Many2one(
        'einvoice.catalog.06',
        'Tipo de Documento',
        index=True,
        default=_default_catalog,
        copy=False
    )

    @api.onchange('is_company')
    def _onchange_is_company_catalog(self):
        """Cambia automáticamente el tipo de documento según Persona/Empresa."""
        code = '6' if self.is_company else '1'
        catalog = self.env['einvoice.catalog.06'].search([('code', '=', code)], limit=1)
        if catalog:
            self.catalog_06_id = catalog

    @api.onchange('catalog_06_id', 'vat')
    def vat_change(self):
        if not self.vat or not self.catalog_06_id:
            return
        code = self.catalog_06_id.code
        # Validar longitud
        if code == '1' and len(self.vat) != 8:
            return
        if code == '6' and len(self.vat) != 11:
            return
        # Consultar APIPERU
        res = self.get_apiperu_data(code, self.vat)
        if res:
            self.update(res)
        else:
            # Fallback: usar el número de documento como nombre placeholder
            if not self.name:
                self.name = self.vat
            if not self.registration_name:
                self.registration_name = self.vat

    def update_document(self):
        for partner in self:
            if not partner.vat:
                continue

            if partner.catalog_06_id and partner.catalog_06_id.code == '1':
                # Valida DNI
                if partner.vat and len(partner.vat) != 8:
                    raise UserError('El Dni debe tener 8 caracteres')
                else:
                    d = get_data_doc_number('dni', partner.vat, format='json')
                    if not d['error']:
                        d = d['data']
                        partner.name = '%s %s %s' % (
                            d['nombres'],
                            d['ape_paterno'],
                            d['ape_materno']
                        )

            elif partner.catalog_06_id and partner.catalog_06_id.code == '6':
                # Valida RUC
                if partner.vat and len(partner.vat) != 11:
                    raise UserError('El Ruc debe tener 11 caracteres')
                else:
                    d = get_data_doc_number('ruc', partner.vat, format='json')
                    if d['error']:
                        continue
                    d = d['data']
                    # Busca el distrito
                    district_obj = self.env['res.country.state']
                    prov_ids = district_obj.search([
                        ('name', '=', d['provincia']),
                        ('province_id', '=', False),
                        ('state_id', '!=', False)
                    ])
                    dist_id = district_obj.search([
                        ('name', '=', d['distrito']),
                        ('province_id', '!=', False),
                        ('state_id', '!=', False),
                        ('province_id', 'in', prov_ids.ids)
                    ], limit=1)

                    if dist_id:
                        partner.district_id = dist_id.id
                        partner.province_id = dist_id.province_id.id
                        partner.state_id = dist_id.state_id.id
                        partner.country_id = dist_id.country_id.id

                    # Si es HABIDO, caso contrario es NO HABIDO
                    tstate = d['condicion_contribuyente']
                    if tstate == 'HABIDO':
                        tstate = 'habido'
                    else:
                        tstate = 'nhabido'
                    partner.state = tstate

                    partner.name = d['nombre_comercial'] != '-' and d['nombre_comercial'] or d['nombre']
                    partner.registration_name = d['nombre']
                    partner.street = d['domicilio_fiscal']
                    partner.is_company = True
                    partner.ubigeo = d['ubigeo']
                    partner.zip = d['ubigeo']

    @api.model
    def get_apiperu_data(self, document_type, document_number):
        url = self.env.company.apiperu_url if hasattr(self.env.company, 'apiperu_url') else ''
        token = self.env.company.apiperu_token if hasattr(self.env.company, 'apiperu_token') else ''

        if not url or not token:
            return {}

        document_type = 'dni' if document_type == '1' else 'ruc' if document_type == '6' else ''
        if not document_type:
            return {}

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {0}'.format(token),
        }
        register_url = '{}/{}/{}'.format(url, document_type, document_number)

        try:
            response = requests.get(register_url, headers=headers, timeout=10)
        except requests.exceptions.RequestException:
            return {}

        if response.status_code != 200:
            return {}

        response = response.json()
        if not response.get('success'):
            return {}

        data = response.get('data', {})

        if document_type == 'dni':
            return {
                'name': data.get('nombre_completo'),
                'registration_name': data.get('nombre_completo')
            }
        else:
            ubigeo = data.get('ubigeo', [])
            ubigeo = len(ubigeo) > 2 and ubigeo[2]
            district = self.env['res.country.state'].search([('code', '=', ubigeo)], limit=1)
            return {
                'name': data.get('nombre_o_razon_social'),
                'registration_name': data.get('nombre_o_razon_social'),
                'street': data.get('direccion_completa'),
                'district_id': district and district.id or False,
                'province_id': district and district.province_id and district.province_id.id or False,
                'state_id': district and district.state_id and district.state_id.id or False,
                'country_id': district and district.state_id and district.state_id.country_id and district.state_id.country_id.id or False,
                'zip': ubigeo,
                'is_company': True,
                'company_type': 'company',
            }

    @api.model
    def get_apiperu_data_for_button(self, vat, doc_type):
        """Called from OWL widget button — does NOT save the form.
        doc_type: '1' for DNI, '6' for RUC (determined by VAT length client-side).
        Returns data formatted for record.update() in OWL 2."""
        if not doc_type or not vat:
            return {}
        data = self.get_apiperu_data(doc_type, vat)
        if not data:
            return {}
        # Return only scalar fields safe for OWL record.update().
        # Many2one fields (district_id, state_id, etc.) are skipped to
        # avoid OWL format issues — the onchange already handles them.
        safe_fields = ('name', 'registration_name', 'street', 'zip', 'is_company', 'company_type')
        return {k: v for k, v in data.items() if k in safe_fields}
