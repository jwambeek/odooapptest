from odoo import models, fields, api, _


class MrwShipmentNumber(models.Model):
    _inherit = 'stock.picking'
    mrw_label_url = fields.Char(string="Mrw Label Url", help="Url for Generate Label")
    shipment_details = fields.Char(string="Shipment Details", help="Url For View Shipment Details")
