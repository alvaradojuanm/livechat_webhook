from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class LivechatWebhookController(http.Controller):

    @http.route('/livechat/webhook', type='json', auth='public', csrf=False, methods=['POST'])
    def push_message(self, channel_id=None, message=None, **kwargs):
        _logger.info(f"[livechat_webhook] Mensaje recibido en canal {channel_id}: {message}")

        channel = request.env['mail.channel'].sudo().browse(int(channel_id) if channel_id else 0)
        if not channel.exists():
            _logger.error("Canal no encontrado.")
            return {'status': 'error', 'error': 'Canal no encontrado'}

        script = channel._get_chatbot_script()
        if script and script.webhook_enabled and script.webhook_url:
            try:
                reply = script._send_to_webhook(message, channel)
                if reply:
                    script._post_webhook_message(channel, reply)
                    return {'status': 'ok', 'reply': reply}
                return {'status': 'no_reply'}
            except Exception as e:
                _logger.error(f"Error procesando webhook: {e}")
                return {'status': 'error', 'error': str(e)}
        return {'status': 'disabled'}
