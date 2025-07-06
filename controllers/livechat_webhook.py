from odoo import http
from odoo.http import request
import logging
import json

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
            script = request.env['chatbot.script'].sudo().search([
                ('webhook_enabled', '=', True)
            ], limit=1)
            
            if not script:
                _logger.warning("No se encontró script de chatbot con webhook habilitado")
                return {'status': 'disabled'}
                
            _logger.info(f"Script encontrado: {script.title}")
            
            if script.webhook_enabled and script.webhook_url:
                _logger.info(f"Enviando mensaje al webhook: {script.webhook_url}")
                try:
                    reply = script._send_to_webhook(message, channel)
                    _logger.info(f"Respuesta del webhook: {reply}")
                    if reply:
                        script._post_webhook_message(channel, reply)
                        return {'status': 'ok', 'reply': reply}
                    _logger.warning("El webhook no devolvió respuesta.")
                    return {'status': 'no_reply'}
                except Exception as e:
                    _logger.error(f"Error procesando webhook: {e}", exc_info=True)
                    return {'status': 'error', 'error': str(e)}
            else:
                _logger.warning(f"Webhook deshabilitado o URL no configurada")
                return {'status': 'disabled'}
                
        except Exception as e:
            _logger.error(f"Error general: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}