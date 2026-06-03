# -*- coding: utf-8 -*-
{
    'name': 'POS Invoice Payment',
    'version': '18.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': 'Register payments for invoices from POS',
    'description': """
        This module allows to register payments for unpaid invoices directly from the POS interface.
        - Add Invoice button in POS product screen
        - Display unpaid invoices (filtered by customer if selected)
        - Select multiple invoices for payment
        - Register payments with journal selection
    """,
    'author': 'Optin Solutions',
    #'website': 'https://www.optinsolution.com',
    'support': 'optinassist@gmail.com',
    'price': 45,
    'currency': 'USD',
    'depends': ['point_of_sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_views.xml',
        'views/pos_session_views.xml',
        #'views/pos_session_closing_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_payment/static/src/**/*',
        ],
    },
    'installable': True,
    'images': ['static/description/banner.png'],
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
