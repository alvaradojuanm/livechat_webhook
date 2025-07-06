from odoo import models, fields, api
import requests
import logging
import json
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)

class ChatbotScript(models.Model):
    _inherit = 'chatbot.script'

    webhook_url = fields.Char('Webhook URL')
    webhook_enabled = fields.Boolean('Webhook Habilitado', default=False)
    webhook_timeout = fields.Integer('Timeout (s)', default=30)
    webhook_headers = fields.Text('Headers adicionales', help="Headers en formato JSON. Ejemplo: {\"Authorization\": \"Bearer token\"}")

    def _send_to_webhook(self, message_body, discuss_channel):
        """
        Envía el mensaje recibido al webhook externo configurado en el script.
        Devuelve la respuesta del webhook o None si hay error.
        """
        _logger.info(f"[Webhook] Intentando enviar mensaje al webhook para canal {discuss_channel.id}...")
        if not self.webhook_enabled or not self.webhook_url:
            _logger.info("Webhook no está habilitado o URL no configurada.")
            return None

        # Validar URL
        try:
            parsed_url = urlparse(self.webhook_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                _logger.error(f"URL del webhook inválida: {self.webhook_url}")
                return None
        except Exception as e:
            _logger.error(f"Error validando URL del webhook: {e}")
            return None

        payload = {
            'message': message_body,
            'channel_id': discuss_channel.id,
            'channel_name': discuss_channel.name,
            'timestamp': fields.Datetime.now().isoformat()
        }
        headers = {'Content-Type': 'application/json'}
        if self.webhook_headers:
            try:
                additional_headers = json.loads(self.webhook_headers)
                headers.update(additional_headers)
            except Exception as e:
                _logger.error(f"Error procesando headers adicionales: {e}")

        # Permitir método HTTP configurable en el futuro
        method = getattr(self, 'webhook_method', 'POST').upper()
        _logger.info(f"[Webhook] Enviando payload a {self.webhook_url} con método {method}: {payload} y headers: {headers}")
        try:
            if method == 'POST':
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.webhook_timeout
                )
            elif method == 'GET':
                response = requests.get(
                    self.webhook_url,
                    params=payload,
                    headers=headers,
                    timeout=self.webhook_timeout
                )
            else:
                _logger.error(f"Método HTTP no soportado: {method}")
                return None
            _logger.info(f"Respuesta del webhook ({response.status_code}): {response.text}")
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return response_data.get('reply') or response_data.get('message') or response.text
                except Exception as e:
                    _logger.warning(f"No se pudo decodificar JSON de la respuesta: {e}")
                    return response.text
            else:
                _logger.error(f"Error webhook {response.status_code}: {response.text}")
                return None
        except requests.exceptions.Timeout:
            _logger.error("Timeout al conectar con el webhook.")
        except Exception as e:
            _logger.error(f"Error conectando al webhook: {e}", exc_info=True)
        return None

    def _post_webhook_message(self, discuss_channel, message_body):
        """Envía la respuesta del webhook al canal de chat"""
        try:
            # Buscar o crear el partner del bot
            bot_partner = self.env['res.partner'].search([('name', '=', 'ChatBot')], limit=1)
            if not bot_partner:
                bot_partner = self.env['res.partner'].create({
                    'name': 'ChatBot',
                    'is_company': False,
                    'supplier_rank': 0,
                    'customer_rank': 0
                })

            # Enviar mensaje al canal
            discuss_channel.message_post(
                body=message_body,
                author_id=bot_partner.id,
                message_type='comment'
            )
            _logger.info(f"Mensaje enviado al canal {discuss_channel.id}: {message_body}")
        except Exception as e:
            _logger.error(f"Error enviando mensaje al canal: {e}", exc_info=True)
