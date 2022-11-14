# -*- coding: utf-8 -*-
from odoo import models, fields


class SeurResCompany(models.Model):
    _inherit = 'res.company'

    seur_username = fields.Char(string="SEUR Username",)
    seur_password = fields.Char(string="SEUR Password",)
    seur_tax_identifier_number = fields.Char(string="SEUR Tax Identifier Number (NIF)")
    seur_franchise_code = fields.Char(string="SEUR Franchise Code")
    seur_account_code= fields.Char(string="SEUR Account Code", default='-1')
    seur_customer_integration_code = fields.Char(string='SEUR Customer Integration Code')
    seur_customer_code = fields.Char(string="SEUR Customer Code")
    seur_api_url = fields.Char(string="SEUR API URL", default="http://cit.seur.com",help="Enter SEUR API URL ")

    use_seur_parcel_service = fields.Boolean(copy=False, string="Are You Using SEUR?",
                                                  help="If use SEUR Parcel Service than value set TRUE.",
                                                  default=False)
