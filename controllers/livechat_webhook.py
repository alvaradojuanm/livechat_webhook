from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class LivechatWebhookController(http.Controller):

    @http.route('/livechat/webhook', type='json', auth='public', csrf=False, methods=['POST'])
    def push_message(self, channel_id=None, message=None, **kwargs):
        _logger.info(f"[livechat_webhook] Mensaje recibido en canal {channel_id}: {message}")

        if not channel_id:
            _logger.error("No se proporcionó channel_id.")
            return {'status': 'error', 'error': 'No se proporcionó channel_id'}

        if not message:
            _logger.error("No se proporcionó mensaje.")
            return {'status': 'error', 'error': 'No se proporcionó mensaje'}

        # Buscar canal por ID o UUID
        channel = None
        try:
            if str(channel_id).isdigit():
                channel = request.env['mail.channel'].sudo().browse(int(channel_id))
            else:
                channel = request.env['mail.channel'].sudo().search([('uuid', '=', channel_id)], limit=1)
        except Exception as e:
            _logger.error(f"Error obteniendo canal: {e}")
            return {'status': 'error', 'error': str(e)}

        if not channel or not channel.exists():
            _logger.error(f"Canal no encontrado: {channel_id}")
            return {'status': 'error', 'error': 'Canal no encontrado'}

        script = channel._get_chatbot_script()
        _logger.info(f"Script obtenido: {script}")
        if script and script.webhook_enabled and script.webhook_url:
            _logger.info(f"Webhook habilitado: {script.webhook_enabled}, URL: {script.webhook_url}")
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
            _logger.warning(f"Webhook deshabilitado o URL no configurada para el script: {script}")
        return {'status': 'disabled'}
