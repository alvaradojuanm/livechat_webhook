# controllers/livechat_webhook.py
from odoo import http
from odoo.http import request
import logging
import json
import re

_logger = logging.getLogger(__name__)

class LivechatWebhookController(http.Controller):

    @http.route('/livechat/webhook', type='json', auth='public', csrf=False, methods=['POST'])
    def push_message(self, **kwargs):
        _logger.info(f"[livechat_webhook] Datos recibidos: {kwargs}")
        
        channel_id = kwargs.get('channel_id')
        message = kwargs.get('message')
        
        if not channel_id:
            _logger.error("No se proporcionó channel_id.")
            return {'status': 'error', 'error': 'No se proporcionó channel_id'}
        if not message:
            _logger.error("No se proporcionó mensaje.")
            return {'status': 'error', 'error': 'No se proporcionó mensaje'}

        try:
            channel = request.env['mail.channel'].sudo().browse(int(channel_id))
            if not channel.exists():
                _logger.error(f"Canal no encontrado: {channel_id}")
                return {'status': 'error', 'error': 'Canal no encontrado'}

            # Buscar script de chatbot habilitado
            scripts = request.env['chatbot.script'].sudo().search([
                ('webhook_enabled', '=', True)
            ])
            if not scripts:
                _logger.warning("No se encontró script de chatbot con webhook habilitado")
                return {'status': 'disabled'}
            if len(scripts) > 1:
                _logger.warning(f"Se encontraron múltiples scripts habilitados, usando el primero: {scripts[0].title}")
            script = scripts[0]
            _logger.info(f"Script encontrado: {script.title}")

            # Validar que la URL sea válida
            url_regex = re.compile(r'^(https?://)')
            if not (script.webhook_enabled and script.webhook_url and url_regex.match(script.webhook_url)):
                _logger.warning(f"Webhook deshabilitado o URL no configurada/correcta: {script.webhook_url}")
                return {'status': 'disabled', 'error': 'Webhook deshabilitado o URL incorrecta'}

            _logger.info(f"Enviando mensaje al webhook: {script.webhook_url}")
            try:
                if not hasattr(script, '_send_to_webhook'):
                    _logger.error("El método _send_to_webhook no está implementado en chatbot.script")
                    return {'status': 'error', 'error': 'Método _send_to_webhook no implementado'}
                reply = script._send_to_webhook(message, channel)
                _logger.info(f"Respuesta del webhook: {reply}")
                if reply:
                    if hasattr(script, '_post_webhook_message'):
                        script._post_webhook_message(channel, reply)
                    else:
                        _logger.warning("El método _post_webhook_message no está implementado en chatbot.script")
                    return {'status': 'ok', 'reply': reply}
                _logger.warning("El webhook no devolvió respuesta.")
                return {'status': 'no_reply'}
            except Exception as e:
                _logger.error(f"Error procesando webhook: {e}", exc_info=True)
                return {'status': 'error', 'error': str(e)}
                
        except Exception as e:
            _logger.error(f"Error general: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}