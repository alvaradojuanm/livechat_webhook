# controllers/livechat_webhook.py
from odoo import http
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)

class LivechatWebhookController(http.Controller):

    @http.route('/livechat/webhook', type='json', auth='public', csrf=False, methods=['POST'])
    def push_message(self, **kwargs):
        _logger.info(f"[WEBHOOK] === INICIO DE SOLICITUD WEBHOOK ===")
        _logger.info(f"[WEBHOOK] Datos recibidos: {kwargs}")
        _logger.info(f"[WEBHOOK] Headers: {request.httprequest.headers}")
        
        channel_id = kwargs.get('channel_id')
        message = kwargs.get('message')
        
        if not channel_id:
            _logger.error("[WEBHOOK] ERROR: No se proporcionó channel_id.")
            return {'status': 'error', 'error': 'No se proporcionó channel_id'}
        if not message:
            _logger.error("[WEBHOOK] ERROR: No se proporcionó mensaje.")
            return {'status': 'error', 'error': 'No se proporcionó mensaje'}

        _logger.info(f"[WEBHOOK] Procesando mensaje: '{message}' en canal: {channel_id}")

        try:
            # Buscar el canal
            channel = request.env['mail.channel'].sudo().browse(int(channel_id))
            _logger.info(f"[WEBHOOK] Canal encontrado: {channel.name if channel.exists() else 'NO EXISTE'}")
            
            if not channel.exists():
                _logger.error(f"[WEBHOOK] ERROR: Canal no encontrado: {channel_id}")
                return {'status': 'error', 'error': 'Canal no encontrado'}

            # Buscar script de chatbot habilitado
            scripts = request.env['chatbot.script'].sudo().search([
                ('webhook_enabled', '=', True)
            ])
            
            _logger.info(f"[WEBHOOK] Scripts encontrados con webhook habilitado: {len(scripts)}")
            for script in scripts:
                _logger.info(f"[WEBHOOK] Script: {script.title} - URL: {script.webhook_url}")
            
            if not scripts:
                _logger.warning("[WEBHOOK] No se encontró script de chatbot con webhook habilitado")
                return {'status': 'disabled', 'message': 'No hay scripts con webhook habilitado'}
            
            script = scripts[0]  # Usar el primer script encontrado
            _logger.info(f"[WEBHOOK] Usando script: {script.title}")
            
            if script.webhook_enabled and script.webhook_url:
                _logger.info(f"[WEBHOOK] Enviando mensaje al webhook: {script.webhook_url}")
                try:
                    reply = script._send_to_webhook(message, channel)
                    _logger.info(f"[WEBHOOK] Respuesta del webhook: {reply}")
                    if reply:
                        script._post_webhook_message(channel, reply)
                        _logger.info(f"[WEBHOOK] Mensaje enviado al canal exitosamente")
                        return {'status': 'ok', 'reply': reply}
                    _logger.warning("[WEBHOOK] El webhook no devolvió respuesta.")
                    return {'status': 'no_reply', 'message': 'Webhook no devolvió respuesta'}
                except Exception as e:
                    _logger.error(f"[WEBHOOK] Error procesando webhook: {e}", exc_info=True)
                    return {'status': 'error', 'error': str(e)}
            else:
                _logger.warning(f"[WEBHOOK] Webhook deshabilitado o URL no configurada")
                return {'status': 'disabled', 'message': 'Webhook deshabilitado o URL no configurada'}
                
        except Exception as e:
            _logger.error(f"[WEBHOOK] Error general: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
        finally:
            _logger.info(f"[WEBHOOK] === FIN DE SOLICITUD WEBHOOK ===")

    @http.route('/livechat/webhook/test', type='http', auth='public', csrf=False, methods=['GET'])
    def test_webhook(self):
        """Endpoint para probar la configuración del webhook"""
        _logger.info("[WEBHOOK TEST] Probando configuración de webhook")
        
        scripts = request.env['chatbot.script'].sudo().search([
            ('webhook_enabled', '=', True)
        ])
        
        result = {
            'status': 'ok',
            'scripts_found': len(scripts),
            'scripts': []
        }
        
        for script in scripts:
            result['scripts'].append({
                'title': script.title,
                'webhook_url': script.webhook_url,
                'webhook_enabled': script.webhook_enabled,
                'webhook_timeout': script.webhook_timeout
            })
        
        return json.dumps(result, indent=2)

    @http.route('/livechat/webhook/debug', type='http', auth='public', csrf=False, methods=['GET'])
    def debug_webhook(self):
        """Endpoint para debug de canales activos"""
        _logger.info("[WEBHOOK DEBUG] Obteniendo información de debug")
        
        # Obtener canales de livechat activos
        channels = request.env['mail.channel'].sudo().search([
            ('channel_type', '=', 'livechat')
        ], limit=10)
        
        result = {
            'status': 'ok',
            'channels_found': len(channels),
            'channels': []
        }
        
        for channel in channels:
            result['channels'].append({
                'id': channel.id,
                'name': channel.name,
                'channel_type': channel.channel_type,
                'create_date': str(channel.create_date) if channel.create_date else None
            })
        
        return json.dumps(result, indent=2)