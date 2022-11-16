from odoo import fields, models


class DHLSpainStock(models.Model):
    _inherit = 'stock.picking'

    dhl_lp_number = fields.Char(string='DHL LP Number')
