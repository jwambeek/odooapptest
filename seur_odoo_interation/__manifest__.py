# -*- coding: utf-8 -*-
{
    'name': 'SEUR Shipping Integration',
    'version': '15.01.03.2022',
    'author': "Vraja Technologies",
    'price': '321',
    'currency': 'EUR',
    'category': "Website",
    'summary': """""",
    'description': """Using SEUR Integration we submit order to Sendle and generate label in odoo and get tracking information in odoo.We are providing following modules mrw,mondial relay,collisimo,dbschenker.""",
    'depends': ['delivery'],
    'data': [
        'views/res_company.xml',
        'views/delivery_carrier.xml',
    ],
    'images': [
        'static/description/cover.jpg',
    ],

    'maintainer': 'Vraja Technologies',
    'website': 'https://www.vrajatechnologies.com',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'cloc_exclude': [
        "./**/*",
    ]

}
# version changelog
# 15.28.05.2021 Initial version of the app
# 15.29.10.2021 add tracking method(migrate in 15 by mithilesh )
# 15.14.02.2022 add new code in seur_product_code (104)
# 15.01.03.2022 add new parameter email and phone in xml request
#  Develope and Tested By Shyam Oganja
