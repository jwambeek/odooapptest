# -*- coding: utf-8 -*-
from odoo import fields, models


class DHLSpainProductPackaging(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(
        selection_add=[("dhl_spain", "DHL Spain")])
