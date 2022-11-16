import json
import logging
from odoo import fields, models
from .dhl_spain_request import DHLSpainRequest
from odoo.exceptions import ValidationError

_logger = logging.getLogger("DHL Spain")


class ResCompanyDHLSpain(models.Model):
    _inherit = 'res.company'

    use_dhl_spain_shipping_provider = fields.Boolean(copy=False, string="Are You Use DHL Spain.?",
                                                     help="If use DHL Spain Integration than value set TRUE.",
                                                     default=False)

    dhl_spain_url = fields.Char(string='DHL Spain API URL', copy=False, default='https://external.dhl.es')
    dhl_spain_username = fields.Char(string='DHL Spain Username', copy=False)
    dhl_spain_password = fields.Char(string='DHL Spain Password', copy=False)
    dhl_spain_customer_number = fields.Char(string='DHL Spain Customer Number', copy=False)
    dhl_spain_token = fields.Char(string='DHL Token', copy=False)

    def generate_dhl_spain_token(self):
        """
        generate auth toke for dhl spain
        """
        request_body = {
            "Username": "%s" % self.dhl_spain_username,
            "Password": "%s" % self.dhl_spain_password
        }
        status, status_code, response = DHLSpainRequest.send_request(self, service='authentication', method='POST',
                                                                     data=json.dumps(request_body), param=False)
        if status:
            self.dhl_spain_token = response
        else:
            raise ValidationError("{0} \n {1}".format(status_code, response))

    def generate_dhl_spain_toke_crone(self):
        for res in self.search([('use_dhl_spain_shipping_provider', '=', True)]):
            try:
                res.generate_dhl_spain_token()
            except Exception as error:
                _logger.error(error)
