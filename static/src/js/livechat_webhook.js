/** @odoo-module **/
import { WebsiteLivechatWidget } from 'website_livechat.widget';
import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';

console.log('Livechat Webhook Module Loading...');

patch(WebsiteLivechatWidget.prototype, {
    
    /**
     * Sobrescribe el método de envío de mensajes para interceptar y enviar al webhook
     */
    async _onSubmitMessage(ev) {
        console.log('_onSubmitMessage interceptado!');
        const msg = this.$input.val().trim();
        console.log('Mensaje capturado:', msg);
        console.log('Channel ID:', this.channel_id);
        
        if (!msg) return;
        
        // Llamar al método original para enviar el mensaje normalmente
        super._onSubmitMessage(ev);
        
        // Enviar el mensaje al webhook si está configurado
        if (this.channel_id) {
            console.log('Enviando al webhook...');
            try {
                const response = await rpc('/livechat/webhook', {
                    channel_id: this.channel_id,
                    message: msg
                });
                
                console.log('Respuesta del webhook:', response);
                
                if (response.status === 'ok' && response.reply) {
                    console.log('Respuesta del webhook procesada correctamente');
                } else if (response.status === 'error') {
                    console.error('Error del webhook:', response.error);
                } else {
                    console.log('Webhook status:', response.status);
                }
            } catch (error) {
                console.error('Error comunicando con el webhook:', error);
            }
        } else {
            console.log('No hay channel_id disponible');
        }
    },

    /**
     * Método alternativo para interceptar mensajes
     */
    _sendMessage(message) {
        console.log('_sendMessage interceptado!', message);
        super._sendMessage(message);
        this._triggerWebhook(message);
    },

    /**
     * Método para enviar al webhook
     */
    async _triggerWebhook(message) {
        if (!this.channel_id) {
            console.log('No channel_id para webhook');
            return;
        }

        console.log('Triggering webhook for message:', message);
        try {
            const response = await rpc('/livechat/webhook', {
                channel_id: this.channel_id,
                message: message
            });
            
            console.log('Webhook response:', response);
        } catch (error) {
            console.error('Webhook error:', error);
        }
    }
});

// Método alternativo usando eventos del DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up livechat webhook listeners...');
    
    // Interceptar envío de mensajes mediante eventos
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.classList.contains('o_livechat_chatwindow_input') || 
            form.closest('.o_livechat_chatwindow')) {
            console.log('Livechat form submission detected');
            
            const input = form.querySelector('input[type="text"]');
            if (input && input.value.trim()) {
                console.log('Message to send:', input.value.trim());
                // Aquí podrías hacer la llamada al webhook
                handleWebhookMessage(input.value.trim());
            }
        }
    });
    
    // Interceptar tecla Enter en inputs del livechat
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.closest('.o_livechat_chatwindow')) {
            const input = e.target;
            if (input.value && input.value.trim()) {
                console.log('Enter pressed in livechat:', input.value.trim());
                setTimeout(() => {
                    handleWebhookMessage(input.value.trim());
                }, 100);
            }
        }
    });
});

async function handleWebhookMessage(message) {
    console.log('Handling webhook message:', message);
    
    // Intentar obtener el channel_id del DOM
    const chatWindow = document.querySelector('.o_livechat_chatwindow');
    let channelId = null;
    
    if (chatWindow) {
        // Buscar el channel_id en varios lugares posibles
        channelId = chatWindow.dataset.channelId || 
                   chatWindow.getAttribute('data-channel-id') ||
                   chatWindow.querySelector('[data-channel-id]')?.dataset.channelId;
    }
    
    console.log('Channel ID found:', channelId);
    
    if (!channelId) {
        console.log('No channel ID found, trying alternative method...');
        // Método alternativo: buscar en el objeto global de Odoo
        if (window.odoo && window.odoo.livechat) {
            channelId = window.odoo.livechat.channel_id;
            console.log('Channel ID from global object:', channelId);
        }
    }
    
    if (channelId) {
        try {
            const response = await rpc('/livechat/webhook', {
                channel_id: parseInt(channelId),
                message: message
            });
            
            console.log('Webhook response:', response);
        } catch (error) {
            console.error('Webhook error:', error);
        }
    } else {
        console.log('Could not find channel ID for webhook');
    }
}

console.log('Livechat Webhook Module Loaded!');