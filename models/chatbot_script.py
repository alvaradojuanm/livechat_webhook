from odoo import models, fields
import requests
import logging
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)

class ChatbotScript(models.Model):
    _inherit = 'chatbot.script'

    webhook_url = fields.Char('Webhook URL')
    webhook_enabled = fields.Boolean('Webhook Habilitado', default=False)
    webhook_timeout = fields.Integer('Timeout (s)', default=30)
    webhook_headers = fields.Text('Headers adicionales', help="Headers en formato JSON. Ejemplo: {\"Authorization\": \"Bearer token\"}")

    def _send_to_webhook(self, message_body, discuss_channel):
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
        }
        headers = {'Content-Type': 'application/json'}
        if self.webhook_headers:
            try:
                headers.update(eval(self.webhook_headers))
            except Exception as e:
                _logger.error(f"Error procesando headers adicionales: {e}")

        _logger.info(f"Enviando payload al webhook {self.webhook_url}: {payload}")
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=self.webhook_timeout
            )
            _logger.info(f"Respuesta del webhook ({response.status_code}): {response.text}")
            if response.status_code == 200:
                return response.json().get('reply') or response.text
            else:
                _logger.error(f"Error webhook {response.status_code}: {response.text}")
                return None
        except requests.exceptions.Timeout:
            _logger.error("Timeout al conectar con el webhook.")
        except Exception as e:
            _logger.error(f"Error conectando al webhook: {e}", exc_info=True)
        return None

    def _post_webhook_message(self, discuss_channel, message_body):
        bot_partner = self.env['res.partner'].search([('name', '=', 'ChatBot')], limit=1)
        if not bot_partner:
            bot_partner = self.env['res.partner'].create({'name': 'ChatBot'})

        discuss_channel.message_post(
            body=message_body,
            author_id=bot_partner.id,
            message_type='comment'
        )

    def _get_chatbot_script(self):
        script = super()._get_chatbot_script()
        if not script:
            script = self.env['chatbot.script'].search([('webhook_enabled', '=', True)], limit=1)
        return script
