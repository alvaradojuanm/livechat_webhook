/** @odoo-module **/
import { WebsiteLivechatWidget } from 'website_livechat.widget';
import { patch } from '@web/core/utils/patch';

patch(WebsiteLivechatWidget.prototype, 'livechat_webhook_integration', {
  _onSubmitMessage(ev) {
    const msg = this.$input.val().trim();
    if (!msg) return;
    this._super(ev);
    this._rpc({
      route: '/livechat/webhook',
      params: { channel_id: this.channel_id, message: msg }
    }).then(res => {
      if (res.reply) {
        this._appendMessage(res.reply, 'operator');
      }
    }).catch(() => {
      this._appendMessage("Error comunicando con el webhook.", 'operator');
    });
  },
});
