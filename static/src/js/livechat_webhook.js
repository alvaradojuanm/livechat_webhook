/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { Livechat } from '@website_livechat/components/livechat/livechat';

patch(Livechat.prototype, {
    async onMessageSent(message) {
        await this._super(...arguments);

        const msgContent = message?.content || '';
        const channelUUID = this.channel?.uuid || null;

        if (!msgContent || !channelUUID) return;

        this.rpc('/livechat/webhook', {
            channel_id: channelUUID,
            message: msgContent
        }).then(res => {
            if (res.reply) {
                this.addMessage({
                    content: res.reply,
                    author_id: 'operator',
                    is_operator: true,
                });
            }
        }).catch(() => {
            this.addMessage({
                content: "Error comunicando con el webhook.",
                author_id: 'operator',
                is_operator: true,
            });
        });
    }
});
