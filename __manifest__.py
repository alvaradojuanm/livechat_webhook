{
    'name': 'Live Chat Webhook Integration',
    'version': '18.0.1.0.0',
    'category': 'Website/Live Chat',
    'summary': 'Integra Live Chat con webhooks externos (N8N)',
    'description': """
        Este módulo permite integrar el Live Chat de Odoo con webhooks externos.
        Intercepta los mensajes del chatbot y los envía a un webhook configurado,
        devolviendo la respuesta del webhook al usuario.
    """,
    'author': 'DployXperts',
    'website': 'https://dployxperts.com',
    'depends': [
        'im_livechat',
        'website_livechat',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/chatbot_script_data.xml',
        'views/livechat_channel_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'livechat_webhook/static/src/js/livechat_webhook.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}