# -*- coding: utf-8 -*-

import base64
import json
import requests

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from requests.exceptions import HTTPError, Timeout

SERVERS_CERTIFICATION_SELECTION = [
    ('https://ws.gecoerp.com/api/', 'GECOERP SRV1'),
    ('https://ws.gecoerp.mx/api/', 'GECOERP SRV2')
]

class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_pac = fields.Selection(
        selection_add = [('gecoerp', 'GECOERP')]
    )

    servidor_de_timbrado_ent = fields.Selection(
        selection = SERVERS_CERTIFICATION_SELECTION,
        string = _('Servidor de Timbrado'),
        default = 'https://ws.gecoerp.com/api/',
    )

    timbres_produccion = fields.Integer(
        string = _('Timbres para Producción'),
        readonly = True
    )

    vigencia_timbres_produccion = fields.Date(
        string=_('Vigencia de Timbres'),
        readonly=True
    )

    timbres_pruebas = fields.Integer(
        string = _('Timbres para Pruebas'),
        readonly = True
    )

    vigencia_timbres_pruebas = fields.Date(
        string='Vigencia de Timbres para Pruebas',
        readonly=True
    )

    redundancia_timbrado = fields.Boolean(
        string = _('- Redundancia y Alta Diponivilidad de Timbrado Multi-PAC (Costo adicional)')
    )

    mantener_copia_de_cfdi = fields.Boolean(
        string = _('- Mantener Copia del CFDI con el PAC. (Costo adicional)')
    )

    api_key = fields.Char(
        string=_('API Key'),
        default='Sin Registrar',
        readonly=True
    )

    tipo_licencia= fields.Selection(
        selection=[('00', 'Licencia por Consumo'),
                   ('01', 'Licencia Pago Anual'),
                   ('02', 'Licencia Pago Anual con Soporte'),
                   ('03', 'Licencia Pago Mensual'),
                   ('04', 'Licencia Pago Mensual con Soporte'),
                   ('05', 'Licencia Multi RFC Pago Anual'),
                   ('06', 'Licencia Multi RFC Pago Anual con Soporte'),
                   ('07', 'Licencia Multi RFC Pago Mensual'),
                   ('08', 'Licencia Multi RFC Pago Mensual con Soporte'),
                   ('09', 'Licencia Pago Anual Un RFC, Timbrado Ilimitado'),
                   ('10', 'Licencia Pago Anual Un RFC, Timbrado Ilimitado con Soporte'),],
        string='Tipo de Licenciamiento', default='00', readonly=True
    )

    fecha_ini_licencia = fields.Date(
        string=_('Fecha de Registro'),
        readonly=True
    )

    fecha_fin_licencia = fields.Date(
        string=_('Fecha de Vencimiento'),
        readonly=True
    )

    log = fields.Char(
        string = _('Log (Última Patición)'),
        readonly=True
    )

    @api.model
    def get_timbres_by_cron(self):
        companies = self.search([('l10n_mx_edi_pac', '!=', 'gecoerp')])
        for company in companies:
            company.get_timbres()
        return True

    def get_timbres(self):
        headers = {"Content-type": "application/json"}
        url = '%s' % (self.servidor_de_timbrado_ent)
        data = {
            'emisor': {
                'rfc': self.vat.upper()
            },
            'conf': {            
                'apli': 'CONS-T',
                'url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                'uuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),            
                'sistema': 'Odoo Enterprice',
                'version': 'V17'            
            }
        }
        try:
            response = requests.post(url,auth=None,verify=False, data=json.dumps(data),headers=headers)
            json_response = response.json()
        except Exception as e:
            print(e)
            json_response = {}
    
        if not json_response:
            return
        
        if json_response['code'] == '200':
            value = {
                'timbres_produccion': json_response['folios'],
                'timbres_pruebas': json_response['folios_pruebas'],
                'log': json_response['message']
            }
            self.update(value)
        else:
            value = {
                'log': json_response['code'] + " - " + json_response['message']
            }
            self.update(value)

        return True

    def register_company_ent(self):

        existe_error = False
        message = ''

        if not self.vat:
            existe_error = True
            message = 'El Emisor no tiene RFC Configurado. '

        if not self.name:
            existe_error = True
            message = message + 'La Razon Social del Emisor es Requerida. '

        if existe_error:
            raise UserError(message)

        headers = {"Content-type": "application/json"}
        url = '%s' % (self.servidor_de_timbrado_ent)
        data = {
            'emisor': {
                'rfc': self.vat.upper(),
                'razon_social': self.name, 
            },        
            'conf': {
                'apli': 'ALT',
                'sistema': 'Odoo Enterprice',
                'version': 'V17',
                'url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                'uuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
            },
            'servicios': {
                'redundancia': self.redundancia_timbrado,    
                'copia_cfdi': self.mantener_copia_de_cfdi,
            }
        }

        try:
            response = requests.post(url, data=json.dumps(data), headers=headers, timeout=(10,60), auth=None, verify=False)
            response.raise_for_status()
        except Timeout:
           raise UserError('El servidor de timbrado no responde favor de intenlarlo nuevamente más tarde. Si el problema persiste contacte a sus administrador.')
        except HTTPError as http_err:
           raise UserError(http_err)
        except Exception as err:
           raise UserError(err)

        json_response = response.json()

        if json_response['code'] == '200':
           val = {
               'api_key': json_response['apikey'],
               'tipo_licencia': json_response['tipo_licencia'],
               'fecha_ini_licencia': json_response['fecha_ini'],
               'fecha_fin_licencia': json_response['fecha_fin'],
               'log': json_response['message']
           }
           self.update(val)
        elif json_response['code'] == '510':
           val = {
               'api_key': '',
               'fecha_fin_licencia': json_response['fecha_fin'],
               'log': json_response['code'] + " - " + json_response['message']
           }
           self.update(val)
           #raise UserError(json_response['code'] + " - " + json_response['message'])
        else:
           val = {'log': json_response['code'] + " - " + json_response['message']}
           self.update(val)
           raise UserError(json_response['code'] + " - " + json_response['message'])

        return True

    def button_consulta(self):
        self.get_timbres()
        return True

    def button_registra(self):
        self.register_company_ent()
        return True
