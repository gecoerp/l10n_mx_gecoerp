# -*- coding: utf-8 -*-

import requests
import json
import base64

from odoo import api, models, _
from odoo.exceptions import UserError

class L10nMxEdiDocument(models.Model):
    _inherit = 'l10n_mx_edi.document'

    @api.model
    def _get_gecoerp_credentials(self, company):
        if not company.api_key:
            return {
                'errors': [_("The api key are missing.")]
            }
        url = '%s' % (company.servidor_de_timbrado_ent)
        return {
            'rfc': company.vat.upper(),
            'apikey': company.api_key,
            'url': url,
            'modo_prueba': company.l10n_mx_edi_pac_test_env,
        }

    @api.model
    def _gecoerp_sign(self, credentials, cfdi):

        headers = {"Content-type": "application/json"}
        url = credentials['url']

        data = {
            'emisor': {
                'rfc': credentials['rfc']
            },
            'xml': cfdi.decode("utf-8"),  
            'conf': {
                'apli': 'TIM-DOC',   
                'apikey': credentials['apikey'],          
                'url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                'uuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
                'modo_prueba': credentials['modo_prueba'],
            }
        }

        try:
            response = requests.post(url, auth=None, verify=False, data=json.dumps(data), headers=headers)
        except Exception as e:
            error = str(e)
            if "Name or service not known" in error or "Failed to establish a new connection" in error:
                return {
                    'errors': [_("Servidor fuera de servicio, favor de intentar mas tarde")],
                }
            else:
                raise UserError(error)

        json_response = response.json()

        if json_response['code'] != '200':
            errors = []
            errors.append(_("Code : %s", json_response['code']))
            errors.append(_("Message : %s", json_response['message']))
            return {'errors': errors}

        if json_response.get('xml'):
            return {
                'cfdi_str': base64.b64decode(json_response.get('xml'))
            }

    def _gecoerp_cancel(self, company, credentials, uuid, cancel_reason, cancel_uuid=None):

        headers = {"Content-type": "application/json"}
        url = '%s' % (self.servidor_de_timbrado_ent)

        certificates = company.l10n_mx_edi_certificate_ids
        certificate = certificates.sudo()._get_valid_certificate()

        data = {
            'emisor': {
                'rfc': credentials['rfc']
            },         
            'conf': {
                'apli': 'CAN-DOC',   
                'apikey': credentials['apikey'],          
                'url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                'uuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
                'modo_prueba': credentials['modo_prueba'],            
                'uuid': uuid,
                'motivo': cancel_reason,
                'foliosustitucion': cancel_uuid,
                'certificados': {
                    'archivo_cer': certificate.content.decode('UTF-8'),
                    'archivo_key': certificate.key.decode('UTF-8'),
                    'contrasena': certificate.password,
                }
            }
        }

        try:
            response = requests.post(url, auth=None, verify=False, data=json.dumps(data), headers=headers)
        except Exception as e:
            return {
                'errors': [_("The GECOERP service failed to cancel with the following error: %s", str(e))],
            }

        code = None
        msg = None

        response_json = response.json()

        if response_code not in ('201', '202'):
            code = response_code
            if response.resultados:
                result = response.resultados[0]
            else:
                result = response
            if 'mensaje' in result:
                msg = result.mensaje

        errors = []
        if code:
            errors.append(_("Code : %s", code))
        if msg:
            errors.append(_("Message : %s", msg))
        if errors:
            return {'errors': errors}

        return {}
