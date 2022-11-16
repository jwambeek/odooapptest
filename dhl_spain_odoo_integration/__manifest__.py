# -*- coding: utf-8 -*-pack
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{

    # App information
    'name': 'DHL Spain Shipping Integration',
    'category': 'Website',
    'version': '15.0.18.04.22',
    'summary': '',
    'license': 'OPL-1',

    'depends': ['delivery'],
    'data': [
        'data/ir_cron.xml',
        'views/stock.xml',
        'views/delivery_carrier.xml',
        'views/res_company.xml'

    ],



    # Odoo Store Specific
    'images': ['static/description/cover.jpg'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'https://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '149',
    'currency': 'EUR',

}
# version changelog
#15.0.18.04.22