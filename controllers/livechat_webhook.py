from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class LivechatWebhookController(http.Controller):

    @http.route('/livechat/webhook', type='json', auth='public', csrf=False, methods=['POST'])
    def push_message(self, channel_id=None, message=None, **kwargs):
        _logger.info(f"[livechat_webhook] Message received on channel {channel_id}: {message}")
        Channel = request.env['im_livechat.channel'].sudo().browse(int(channel_id) if channel_id else 0)
        script = Channel._get_chatbot_script()
        if script and script.webhook_enabled and script.webhook_url:
            try:
                reply = script._send_to_webhook(message, Channel)
                if reply:
                    script._post_webhook_message(Channel, reply)
                    return {'status': 'ok', 'reply': reply}
                return {'status': 'no_reply'}
            except Exception as e:
                _logger.error(f"[livechat_webhook] Error in webhook processing: {e}")
                return {'status': 'error', 'error': str(e)}
        return {'status': 'disabled'}