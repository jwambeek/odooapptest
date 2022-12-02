import base64
from requests import request
from odoo.exceptions import ValidationError
from odoo import models, fields,api

class ResCompany(models.Model):
    _inherit = "res.company"

    deutschepost_client_id = fields.Char(string="Deutschepost API Key", help="Deutschepost API Key providing by Deutschepost.",copy=False)
    deutschepost_client_secret = fields.Char(string="Deutschepost Client Secret",
                                         help="Deutschepost Client secret provding by Deutschepost.", copy=False)
    deutschepost_api_url = fields.Char(copy=False,string='Deutschepost API URL', help="API URL, Redirect to this URL when calling the API.",default="https://api-sandbox.dhl.com")
    deutschepost_accesstoken = fields.Char(string="Deutschepost Access Token ",readonly=True,
                                         help="Deutschepost accesstoken provding by Deutschepost.", copy=False)
    use_deutschepost_shipping_provider = fields.Boolean(copy=False, string="Are You Use Deutschepost.?",
                                                        help="If use Deutschepost shipping Integration than value set TRUE.",
                                                        default=False)

    def get_deutscepost_access_token(self):
        url ="%s/dpi/v1/auth/accesstoken"%(self.deutschepost_api_url)
        api_secret = self.deutschepost_client_secret
        api_key = self.deutschepost_client_id
        data = "%s:%s" % (api_key, api_secret)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
        headers = {"Authorization": authrization_data,
                   "Content-Type": "application/json"}
        try:
            response_data = request(method='GET', url=url, headers=headers)
            if response_data.status_code == 200:
                responses = response_data.json()
                self.deutschepost_accesstoken = "Bearer %s"%(responses.get('access_token'))
            else:
                raise ValidationError("Response : %s"%(response_data.content))

        except Exception as e:
            raise ValidationError(e)
