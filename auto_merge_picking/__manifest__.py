# -*- coding: utf-8 -*-

{
    "name": "Auto Merge Picking",
    "version": "15.18.12.2021",
    "category": "Inventory",
    "summary": 'Auto Merge Delivery Order Based on Same Partner,Picking Type and Delivery Order Not in Done and Cancel State',
    "license": 'OPL-1',
    "description": """
        Auto Merge Delivery Order Based on Same Partner,Picking Type and Delivery Order Not in Done and Cancel State.. 
    """,
    "author": "Vraja Technologies",
    "depends": ['sale_stock'],
    "data": [
        'data/cron.xml',
        'views/stock_picking.xml'
    ],
    'images': ['static/description/auto_merge_delivery_orders.jpg'],
    'website': 'https://www.vrajatechnologies.com',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    "auto_install": False,
    "installable": True,
    "application": True,
    "price": 11,
    "currency": 'EUR',
}
