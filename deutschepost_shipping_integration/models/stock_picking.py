# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    deutschpost_order_number = fields.Char(string="Deutschpost Order Number", copy=False)
    deutschpost_item_id = fields.Char(string="Deutschpost ItemID", copy=False)

