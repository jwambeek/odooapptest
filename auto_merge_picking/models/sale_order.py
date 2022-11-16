from odoo import models, api, fields, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_merged = fields.Boolean(string='Merged')
