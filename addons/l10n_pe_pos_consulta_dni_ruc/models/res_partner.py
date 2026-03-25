# -*- coding: utf-8 -*-

from odoo import models, api

import requests


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("tipo_doc", "0") == "6":
                vals["company_type"] = "company"
            else:
                vals["company_type"] = "person"
            if not vals.get("registration_name"):
                vals["registration_name"] = vals.get("name")
        return super(ResPartner, self).create(vals_list)

    # @api.model
    # def consulta_datos(self, tipo_documento, nro_documento, format='json'):
    #     if tipo_documento=="dni":
    #         d = self.get_person_name(nro_documento)
    #         if d:
    #             return {"data":{"nombres":d}}
    #         else:
    #             return {"error":True,"message":"No se ha encontrado el DNI"}
            
    #     elif tipo_documento=="ruc":
    #         d = self.consulta_ruc_api(nro_documento)
    #         if d:
    #             return {"data":d}
    #         else:
    #             return {"error":True,"message":"No se ha encontrado el RUC"}
    
    @api.model
    def consulta_datos(self, tipo_documento, nro_documento, format='json'):
        user, password = 'demorest', 'demo1234'
        url = 'http://py-devs.com/api'
        url = '%s/%s/%s' % (url, tipo_documento, str(nro_documento))
        res = {'error': True, 'message': None, 'data': {}}
        res_partner = self.search([('vat', '=', nro_documento)]).exists()
        # Si el nro. de doc. ya existe
        if res_partner:
            res['message'] = 'Nro. doc. ya existe'
            return res
        try:
            response = requests.get(url, auth=(user, password))
        except Exception:
            res['message'] = 'Error en la conexion'
            return res

        if response.status_code == 200:
            res['error'] = False
            res['data'] = response.json()
        elif response.status_code == 500:
            res['message'] = "Error 500 (proveedor ws: http://py-devs.com/api)"
            return res
        else:
            try:
                res['message'] = response.json()['detail']
            except Exception:
                res['error'] = True
        return res
    