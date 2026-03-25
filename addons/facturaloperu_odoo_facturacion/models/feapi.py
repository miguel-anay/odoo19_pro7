# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from requests.exceptions import ConnectionError, HTTPError, Timeout
import requests
import json
import base64
from datetime import datetime


class feapi(models.Model):
    _inherit = 'account.move'

    def _get_l10n_latam_documents_domain(self):
        """Si el diario tiene l10n_pe_document_type_id configurado, devolver solo ese
        tipo de documento (independiente del tipo de identificación del partner).
        Esto evita que l10n_pe restrinja los tipos disponibles según el RUC del cliente
        y que el compute anule el tipo correcto del diario."""
        self.ensure_one()
        if (self.journal_id.l10n_pe_document_type_id
                and self.journal_id.type == 'sale'
                and self.company_id.country_id.code == 'PE'):
            code = self.journal_id.l10n_pe_document_type_id.code
            return [
                ('code', '=', code),
                ('country_id.code', '=', 'PE'),
                ('internal_type', 'in', ['invoice', 'debit_note', 'all']),
            ]
        return super()._get_l10n_latam_documents_domain()

    # campo para consultar estatus de documento
    external_id = fields.Char(string='External Id', readonly=True, copy=False)
    number_feapi = fields.Char(string='Número', readonly=True, copy=False)

    feapi_display_number = fields.Char(
        string='Serie-Correlativo',
        compute='_compute_feapi_display_number',
    )

    @api.depends('number_feapi', 'journal_id.code', 'l10n_latam_document_number', 'state')
    def _compute_feapi_display_number(self):
        for move in self:
            if move.number_feapi:
                # Ya enviado a SUNAT: muestra el número oficial retornado por la API
                move.feapi_display_number = move.number_feapi
            elif (move.state == 'posted'
                    and move.l10n_latam_document_number
                    and move.journal_id.code):
                # Registrado pero aún no enviado: preview basado en serie+correlativo
                move.feapi_display_number = '{}-{}'.format(
                    move.journal_id.code,
                    move.l10n_latam_document_number,
                )
            else:
                move.feapi_display_number = False
    filename = fields.Char(string='Nombre de Archivo', readonly=True, copy=False)
    link_cdr = fields.Char(string='CDR', readonly=True, copy=False)
    link_pdf = fields.Char(string='PDF', readonly=True, copy=False)
    link_xml = fields.Char(string='XML', readonly=True, copy=False)

    api_cdr = fields.Binary(string='CDR', readonly=True, attachment=True)
    api_filename_cdr = fields.Char()
    api_xml = fields.Binary(string='XML', readonly=True, attachment=True)
    api_filename_xml = fields.Char()

    api_json = fields.Text(string='JSON', readonly=True, store=True, copy=False)
    api_qr = fields.Char(string='QR', readonly=True, copy=False)
    api_number_to_letter = fields.Char(string='number_to_letter', readonly=True, copy=False)
    api_hash = fields.Char(string='Hash SUNAT', readonly=True, copy=False)

    # default serie
    @api.model
    def _default_serie(self):
        return self.env['feapi.serie'].search([], limit=1)

    serie_id = fields.Many2one("feapi.serie", string="Número de Serie", required=True, default=_default_serie, copy=False)

    format_pdf = fields.Selection([
            ('ticket', 'Ticket'),
            ('a4', 'A4'),
        ], string='Formato Pdf', default='a4', copy=False)

    # botones para mostrar el estado actual del documento
    state_api = fields.Selection([
            ('register', 'Registrado'),
            ('send', 'Enviado'),
            ('success', 'Aceptado'),
            ('observed', 'Observado'),
            ('reject', 'Rechazado'),
            ('null', 'Anulado'),
            ('nullable', 'Por anular'),
        ], string='Status API', index=True, store=True, readonly=True, default='register', copy=False)

    state_api_update = fields.Selection([
            ('register', 'Registrado'),
            ('send', 'Enviado'),
            ('success', 'Aceptado'),
            ('observed', 'Observado'),
            ('reject', 'Rechazado'),
            ('null', 'Anulado'),
            ('nullable', 'Por anular'),
        ], string='Status API', store=True, index=True, copy=False)

    state_api_is_update = fields.Boolean('Ha sido actualizado por un usuario', default=False, store=True)

    state_api_can_update = fields.Boolean('Actualizar estado (solo Admin)', default=False, store=True)

    @api.onchange('state_api_update')
    def _onchange_state_api_update(self):
        self.update_state_api_update()

    def update_state_api_update(self):
        for rec in self:
            if not rec.state_api_update:
                return False
            if rec.state_api_update and rec.state_api_update != rec.state_api:
                return True

    # generar json
    def action_invoice_update_state(self, values=None):
        if self.state_api_update and self.state_api_update != self.state_api:
            state_api_update = self.state_api_update
            self.write({'state_api': state_api_update})
            if self.state_api_is_update == False:
                self.write({'state_api_is_update': True})
            return {
                "json": state_api_update
            }

    def _get_document_number(self):
        """Extrae (serie, numero) del documento para enviar a la API.
        En Odoo 19 con l10n_latam el name tiene formato 'F 00000045'
        (sequence_prefix='F ' + l10n_latam_document_number='00000045').
        Usamos l10n_latam_document_number directamente para evitar el error de parseo.
        """
        import re
        serie = self.journal_id.code
        doc_num = self.l10n_latam_document_number
        if doc_num and re.search(r'\d', str(doc_num)):
            digits = re.sub(r'\D', '', str(doc_num))
            return serie, int(digits) if digits else '#'
        match = re.search(r'(\d+)\s*$', self.name or '')
        return serie, int(match.group(1)) if match else '#'

    # enviar json
    def action_invoice_send_sunat(self):
        token = self.company_id.api_token
        url = self.company_id.api_url + '/documents'

        _, document_number = self._get_document_number()

        data = self.data_json(document_number)

        html_json = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        self.write({'api_json': html_json})

        api_token = 'Bearer ' + token

        headers = {
            'Content-Type': 'application/json',
            "Authorization": api_token
        }

        try:
            r = requests.post(url, data=html_json, headers=headers, timeout=15)
            response = r.json()
        except (ConnectionError, HTTPError) as e:
            raise UserError('Error Http')
        except (ConnectionError, Timeout) as e:
            raise UserError('El tiempo de envío se ha agotado, el servidor de la Sunat puede encontrarse no disponible temporalemente')

        if response['success'] == False:
            raise UserError(response['message'])

        filename = response['data']['filename']
        self.write({'filename': response['data']['filename']})
        # edito el external_id
        self.write({'external_id': response['data']['external_id']})
        # edito el estado
        state_api = 'reject'
        if response['links']['cdr']:
            code_sunat = response['response']['code']
            code_int = int(code_sunat) if code_sunat and str(code_sunat).isdigit() else None
            if code_int is None or code_int == 0 or code_int >= 4000:
                state_api = 'success'
            elif 100 <= code_int <= 1999:
                state_api = 'observed'

            self.write({'state_api': state_api})
            url_cdr = response['links']['cdr']
            response_cdr = requests.get(url_cdr, headers=headers)
            self.write({'api_cdr': base64.b64encode(response_cdr.content)})
            self.write({'api_filename_cdr': '{}.zip'.format(filename)})
        else:
            self.write({'state_api': state_api})
        # edito el numero
        self.write({'number_feapi': response['data']['number']})
        # edito el cdr
        self.write({'link_cdr': response['links']['cdr']})
        # edito el pdf
        self.write({'link_pdf': response['links']['pdf']})
        # edito el xml
        self.write({'link_xml': response['links']['xml']})
        url_xml = response['links']['xml']
        response_xml = requests.get(url_xml, headers=headers)
        self.write({'api_xml': base64.b64encode(response_xml.content)})
        self.write({'api_filename_xml': '{}.xml'.format(filename)})
        # edito el qr
        self.write({'api_qr': response['data']['qr']})
        # edito el api_number_to_letter
        self.write({'api_number_to_letter': response['data']['number_to_letter']})
        # edito el hash (si la API lo retorna)
        api_hash = (response.get('data') or {}).get('hash') or (response.get('response') or {}).get('hash') or ''
        if api_hash:
            self.write({'api_hash': api_hash})
        # generar PDF preview: descargar PDF de la API y guardarlo como adjunto de Odoo
        url_pdf = response['links']['pdf']
        if url_pdf:
            response_pdf = requests.get(url_pdf, headers=headers)
            if response_pdf.status_code == 200:
                self.write({'invoice_pdf_report_file': base64.b64encode(response_pdf.content)})

        return {
            "response": response,
        }

    # generar json
    def action_invoice_json_generate(self, values=None):
        serie, document_number = self._get_document_number()
        if document_number != '#':
            self.write({'number_feapi': '{}-{}'.format(serie, document_number)})

        data = self.data_json(document_number)
        html_json = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        self.write({'api_json': html_json})

        return {
            "json": html_json
        }

    def _post(self, soft=True):
        """Override _post (llamado por POS y action_post) para:
        1. Auto-asignar l10n_latam_document_type_id si el diario lo requiere y está vacío.
        2. Generar JSON SUNAT antes de publicar (si corresponde).
        """
        # Fix l10n_latam: el POS llama _post() directamente, bypassing action_post.
        # Si el diario requiere tipo de documento y no está asignado, lo resolvemos aquí.
        for move in self:
            if (move.journal_id.l10n_latam_use_documents
                    and not move.l10n_latam_document_type_id
                    and move.journal_id.l10n_pe_document_type_id):
                pe_code = move.journal_id.l10n_pe_document_type_id.code
                latam_doc = self.env['l10n_latam.document.type'].search([
                    ('code', '=', pe_code),
                    ('country_id.code', '=', 'PE'),
                    ('internal_type', 'in', ['invoice', 'debit_note', 'all']),
                ], limit=1)
                if latam_doc:
                    move.l10n_latam_document_type_id = latam_doc.id

        # Generar JSON SUNAT antes de publicar (solo para diarios con l10n_pe_send_sunat)
        for move in self:
            if move.is_invoice() and hasattr(move.journal_id, 'l10n_pe_send_sunat') and move.journal_id.l10n_pe_send_sunat:
                _, document_number = move._get_document_number()

                data = move.data_json(document_number)
                html_json = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
                move.write({'api_json': html_json})

        return super()._post(soft=soft)

    # validar y guardar json - override action_post for Odoo 19
    def action_post(self):
        # action_post llama internamente a _post(), el fix ya está allí.
        return super().action_post()

    def data_json(self, document_number):
        send_mail = self.company_id.api_send_email

        document_type = self.journal_id.l10n_pe_document_type_id.code

        if self.partner_id.registration_name:
            client_name = self.partner_id.registration_name
        else:
            client_name = self.partner_id.name

        if not document_type:
            raise UserError('Configure tipo de documento en Diario contable (Localización peruana)')

        if document_type == '03':
            if self.amount_total > 700:
                if self.partner_id.catalog_06_id.code == '6':
                    raise UserError('El cliente no cuenta con tipo de documento válido')
                if self.partner_id.catalog_06_id.code == '0':
                    raise UserError('El cliente no cuenta con tipo de documento válido')
                if self.partner_id.catalog_06_id.code == 'A':
                    raise UserError('El cliente no cuenta con tipo de documento válido')

        if document_type == '01':
            if self.partner_id.catalog_06_id.code != '6':
                raise UserError('El cliente no cuenta con tipo de documento válido')

        time = datetime.now().strftime('%H:%M:%S')
        products = self.invoice_line_ids
        guides = self.picking_ids
        items = []
        remissions = []
        totals_discount = 0
        totals_igv = 0
        total_gravadas = 0
        total_inafectas = 0
        total_exoneradas = 0
        total_gratuitas = 0
        total_base_isc = 0
        total_isc = 0
        total_tax = 0
        total_isc = 0

        for product in products:
            if not product.tax_ids:
                raise UserError('No ha seleccionado impuestos en la linea del producto')

            total_tax_line = 0
            code_affectation = ''
            price_acum = 0
            amountIgv = 0
            percentIgv = 0
            amountIcbper = 0
            total_amount_icbper = 0

            # recorro los impuestos
            for tax in product.tax_ids:
                # nombre del impuesto
                affectation_name = tax.l10n_pe_tax_type_id.name
                # codigo de afectacion
                code_affectation = tax.code_affectation
                # monto isc
                amountIsc = 0
                percentIsc = 0

                # calculo de base y monto de impuesto por impuesto
                # reduccion impuesto
                tax_float = (int(tax.amount) / 100) + 1
                # si el impuesto no va dentro del precio
                if tax.price_include == False:
                    if tax.include_base_amount == True:
                        if price_acum == 0:
                            tax_amount = (product.price_subtotal * tax.amount) / 100
                            price_acum = product.price_subtotal + tax_amount
                        else:
                            tax_amount = (price_acum * tax.amount) / 100
                            price_acum = price_acum + tax_amount
                    else:
                        if affectation_name == 'ICBPER':
                            amountIcbper = tax.amount * product.quantity
                            tax_amount = 0
                            total_amount_icbper = total_amount_icbper + amountIcbper
                else:
                    # base para el impuesto actual
                    tax_base = product.price_total / tax_float
                    # monto del impuesto actual
                    tax_amount = (tax_base * tax.amount) / 100

                # dependiendo del nombre asigno valores
                if affectation_name == 'INA':
                    total_inafectas = total_inafectas + product.price_subtotal
                elif affectation_name == 'GRA':
                    total_gratuitas = total_gratuitas + product.price_subtotal
                    tax_amount = tax.amount
                elif affectation_name == 'EXO':
                    percentIgv = '18'
                    total_exoneradas = total_exoneradas + product.price_subtotal
                elif affectation_name == 'IGV':
                    percentIgv = int(tax.amount)
                    amountIgv = tax_amount
                    total_gravadas = total_gravadas + product.price_subtotal

                if affectation_name == 'ISC':
                    percentIsc = int(tax.amount)
                    amountIsc = tax_amount

                total_tax_line = total_tax_line + tax_amount
            total_tax = total_tax + total_tax_line
            total_isc = total_isc + float(format(amountIsc, '.2f'))

            monto_descuento_unidad = (product.price_unit * product.discount) / 100
            monto_descuento_linea = monto_descuento_unidad * product.quantity
            discount_ammount_line = format(monto_descuento_linea, '.2f')
            totals_discount = totals_discount + monto_descuento_linea
            totals_igv = totals_igv + float(format(amountIgv, '.2f'))
            product_name = product.name.replace('\n', ' ')
            product_split = product_name.replace('[', '')
            product_code = product_split.split(']')
            base_discount = product.price_unit * product.quantity
            monto_base = format(base_discount, '.2f')
            item = {
                "codigo_interno": product_code[0],
                "descripcion": product_name,
                "codigo_producto_de_sunat": "",
                "unidad_de_medida": product.product_uom_id.code or 'NIU',
                "cantidad": product.quantity,
                "valor_unitario": product.price_subtotal,
                "codigo_tipo_precio": "01",
                "precio_unitario": product.price_unit,
                "codigo_tipo_afectacion_igv": code_affectation,

                "total_base_igv": product.price_subtotal,
                "porcentaje_igv": percentIgv,
                "total_impuestos_bolsa_plastica": amountIcbper,
                "total_igv": float(format(amountIgv, '.2f')),

                "total_impuestos": float(format(total_tax_line, '.2f')),
                "total_valor_item": product.price_subtotal,
                "total_item": format(product.price_total, '.2f'),
            }
            if product.discount > 0:
                item.update({
                    "descuentos": [
                        {
                            "codigo": "00",
                            "descripcion": "Descuento",
                            "factor": product.discount,
                            "monto": discount_ammount_line,
                            "base": monto_base
                        }
                    ]
                })
            if affectation_name == 'ISC':
                item.update({
                    "codigo_tipo_sistema_isc": "",
                    "total_base_isc": product.price_subtotal,
                    "porcentaje_isc": percentIsc,
                    "total_isc": float(format(amountIsc, '.2f')),
                })
            # operaciones gratuitas
            if affectation_name == 'GRA':
                item.update({
                    "porcentaje_igv": 18,
                    "total_base_igv": product.price_unit / 1.18,
                    "total_base_isc": product.price_unit / 1.18,
                    "total_igv": product.price_unit - (product.price_unit / 1.18),
                    "valor_unitario": 0,
                    "total_valor_item": 0,
                    "total_item": 0,
                    "codigo_tipo_precio": "02",
                })
            items.append(item)

        total_ammount = self.amount_untaxed + totals_igv
        total_venta = float(format(total_ammount, '.2f'))

        data = {
            "serie_documento": self.journal_id.code,
            "numero_documento": document_number,
            "fecha_de_emision": str(self.invoice_date) if self.invoice_date else '',
            "hora_de_emision": time,
            "codigo_tipo_operacion": "0101",
            "codigo_tipo_documento": document_type,
            "codigo_tipo_moneda": self.currency_id.name,
            "factor_tipo_de_cambio": "3.35",
            "fecha_de_vencimiento": str(self.invoice_date_due) if self.invoice_date_due else '',
            "numero_orden_de_compra": "-",
            "datos_del_emisor": {
                "codigo_del_domicilio_fiscal": "0000"
            },
            "datos_del_cliente_o_receptor": {
                "codigo_tipo_documento_identidad": self.partner_id.catalog_06_id.code,
                "numero_documento": self.partner_id.vat,
                "apellidos_y_nombres_o_razon_social": client_name,
                "codigo_pais": "PE",
                "ubigeo": self.partner_id.zip or "",
                "direccion": self.partner_id.street or "",
                "correo_electronico": self.partner_id.email or "",
            },
            "totales": {
                "total_descuentos": totals_discount,
                "total_operaciones_gravadas": total_gravadas,
                "total_operaciones_inafectas": total_inafectas,
                "total_operaciones_exoneradas": total_exoneradas,
                "total_operaciones_gratuitas": total_gratuitas,
                "total_igv": totals_igv,
                "total_impuestos_bolsa_plastica": total_amount_icbper,

                "total_base_isc": 0.00,
                "total_isc": total_isc,

                "total_impuestos": float(format(self.amount_tax, '.2f')),
                "total_valor": self.amount_untaxed - total_gratuitas,
                "total_venta": self.amount_total - total_gratuitas,
            },
            "acciones": {
                "formato_pdf": self.format_pdf,
                "enviar_email": send_mail,
            },
            "items": items,
            "leyendas": []
        }
        if total_gratuitas > 0:
            if total_gravadas == 0:
                leyenda_gratuita = {
                    "codigo": "1002",
                    "valor": "TRANSFERENCIA GRATUITA"
                }
                data.update({
                    "leyendas": [leyenda_gratuita]
                })
        if self.journal_id.l10n_pe_document_type_id.code in ['07', '08']:
            data.update({
                "codigo_tipo_documento": self.journal_id.l10n_pe_document_type_id.code,
                "codigo_tipo_nota": self.l10n_pe_debit_note_code or self.l10n_pe_credit_note_code,
                "motivo_o_sustento_de_nota": self.name,
                "documento_afectado": {
                    "external_id": self.l10n_pe_invoice_origin_id.external_id
                }
            })
        if len(guides) > 0:
            for guide in guides:
                guias = {
                    "numero": guide.sunat_number,
                    "codigo_tipo_documento": "09"
                }
            remissions.append(guias)
            data.update({
                "guias": remissions
            })
        return data

    def action_invoice_sent(self):
        """ Attach XML before opening the send email dialog (Odoo 19) """
        self.ensure_one()
        xmlname = self.api_filename_xml
        xml_link = self.link_xml

        if xmlname:
            datas = self.api_xml
            self.env["ir.attachment"].create({
                "name": xmlname,
                "type": "binary",
                "datas": datas,
                "res_model": "account.move",
                "res_id": self.id,
                "mimetype": "text/xml",
            })
        elif xml_link:
            filename = self.filename or self.name
            response = requests.get(xml_link)
            self.write({
                'api_xml': base64.b64encode(response.content),
                'api_filename_xml': '{}.xml'.format(filename),
            })
            self.env["ir.attachment"].create({
                "name": self.api_filename_xml,
                "type": "binary",
                "datas": self.api_xml,
                "res_model": "account.move",
                "res_id": self.id,
                "mimetype": "text/xml",
            })

        return super().action_invoice_sent()

    def action_invoice_query_status(self):
        token = self.company_id.api_token
        url = self.company_id.api_url + '/documents/status'

        serie, document_number = self._get_document_number()
        if document_number != '#':
            self.write({'number_feapi': '{}-{}'.format(serie, document_number)})

        data = {
            "external_id": self.external_id,
            "serie_number": self.number_feapi,
        }

        query_json = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        self.write({'api_json': query_json})

        api_token = 'Bearer ' + token

        headers = {
            'Content-Type': 'application/json',
            "Authorization": api_token
        }

        try:
            r = requests.post(url, data=query_json, headers=headers, timeout=15)
            response = r.json()
        except (ConnectionError, HTTPError) as e:
            raise UserError('Error Http')
        except (ConnectionError, Timeout) as e:
            raise UserError('El tiempo de envío se ha agotado, el servidor de la Sunat puede encontrarse no disponible temporalemente')

        if response['success'] == False:
            raise UserError(response['message'])

        status_number = response['data']['status_id']
        ex_id = response['data']['external_id']

        if status_number == '01':
            response_status = 'register'
        elif status_number == '03':
            response_status = 'send'
        elif status_number == '05':
            response_status = 'success'
        elif status_number == '07':
            response_status = 'observed'
        elif status_number == '09':
            response_status = 'reject'
        elif status_number == '11':
            response_status = 'null'
        elif status_number == '13':
            response_status = 'nullable'

        self.write({'state_api': response_status})
        if self.external_id == False:
            self.write({'external_id': ex_id})
        filename = response['data']['filename']
        self.write({'filename': response['data']['filename']})

        # edito el pdf
        self.write({'link_pdf': response['links']['pdf']})
        # edito el xml
        self.write({'link_xml': response['links']['xml']})
        # edito el estado
        if response['links']['cdr']:
            url_cdr = response['links']['cdr']
            response_cdr = requests.get(url_cdr, headers=headers)
            self.write({'api_cdr': base64.b64encode(response_cdr.content)})
            self.write({'api_filename_cdr': '{}.zip'.format(filename)})
            self.write({'link_cdr': response['links']['cdr']})

        url_xml = response['links']['xml']
        response_xml = requests.get(url_xml, headers=headers)
        self.write({'api_xml': base64.b64encode(response_xml.content)})
        self.write({'api_filename_xml': '{}.xml'.format(filename)})
        # edito el qr
        self.write({'api_qr': response['data']['qr']})
        # edito el api_number_to_letter
        self.write({'api_number_to_letter': response['data']['number_to_letter']})


class ApiConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    api_token = fields.Char(string='API Token')
    api_url = fields.Char(string='API URL', help="Example sub.domain.com/api/documents")

    def get_values(self):
        res = super(ApiConfig, self).get_values()
        res.update(
            api_token=self.env['ir.config_parameter'].sudo().get_param('res.config.settings.api_token'),
            api_url=self.env['ir.config_parameter'].sudo().get_param('res.config.settings.api_url')
        )
        return res

    def set_values(self):
        super(ApiConfig, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.api_token', self.api_token)
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.api_url', self.api_url)
