/** @odoo-module **/
import { WebsiteLivechatWidget } from 'website_livechat.widget';
import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';

patch(WebsiteLivechatWidget.prototype, {
    
    /**
     * Sobrescribe el método de envío de mensajes para interceptar y enviar al webhook
     */
    async _onSubmitMessage(ev) {
        const msg = this.$input.val().trim();
        if (!msg) return;
        
        // Llamar al método original para enviar el mensaje normalmente
        super._onSubmitMessage(ev);
        
        // Enviar el mensaje al webhook si está configurado
        if (this.channel_id) {
            try {
                console.log('Enviando mensaje al webhook:', msg);
                const response = await rpc('/livechat/webhook', {
                    channel_id: this.channel_id,
                    message: msg
                });
                
                console.log('Respuesta del webhook:', response);
                
                if (response.status === 'ok' && response.reply) {
                    // La respuesta ya se envió desde el servidor, no necesitamos hacer nada más
                    console.log('Respuesta del webhook procesada correctamente');
                } else if (response.status === 'error') {
                    console.error('Error del webhook:', response.error);
                }
            } catch (error) {
                console.error('Error comunicando con el webhook:', error);
            }
        }
    },
});