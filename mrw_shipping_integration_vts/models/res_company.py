from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    use_mrw_shipping_provider = fields.Boolean(string="Is Use MRW Shipping Provider",
                                               help="True when we need to use MRW shipping provider",
                                               default=False, copy=False)
    mrw_api_url = fields.Char(string='MRW API URL',
                              default="http://sagec-test.mrw.es/MRWEnvio.asmx?WSDL",
                              help="Get URL details from Mrw")
    mrw_agency_code = fields.Char(string='MRW AgencyCode', help="You can get AgencyCode after log in at MRW")
    mrw_subscriber_code = fields.Char(string='MRW SubscriberCode',
                                      help="You can SubscriberCode after log in at MRW")
    mrw_user_name = fields.Char(string="MRW Username",
                                help="You can get  UserName from  MRW Team")
    mrw_user_password = fields.Char(string="MRW Password",
                                    help="You can get Password from  MRW Team")
