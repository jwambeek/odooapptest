import binascii
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .dhl_spain_request import check_required_value, DHLSpainRequest


class DHLSpainDeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[("dhl_spain", "DHL Spain")],
                                     ondelete={'dhl_spain': 'set default', })
    dhl_spain_packaging_id = fields.Many2one('stock.package.type', string="Default Package Type")
    dhl_spain_service_type = fields.Selection([('M', 'M Maritim service'), ('A', 'A Air Service')],
                                              string='Service Type',
                                              help='Only for Delivery in Canary Islands–Azores-Madeira')
    dhl_spain_product = fields.Selection([('B2B', 'B2B product'), ('B2C', 'B2C product'), ('R2C', 'RETURN product')],
                                         string='Product')
    dhl_spain_incoterm = fields.Selection([('CPT', 'CPT Paid'), ('EXW', 'EXW Exworks')], string='Incoterms',
                                          copy=False)

    def dhl_spain_rate_shipment(self, orders):
        return {'success': True,
                'price': 0.0,
                'error_message': False, 'warning_message': False}

    def dhl_spain_prepare_body(self, picking):
        receiver_id = picking and picking.partner_id
        required_field = ['name', 'city', 'zip', 'country_id']
        missing_field = check_required_value(required_field, receiver_id)
        if missing_field:
            raise ValidationError("%s has no %s" % (receiver_id.name, ', '.join(required_field)))
        no_of_packages = (len(picking.package_ids) + (1 if picking.weight_bulk else 0))
        request_data = {
            "Customer": "%s" % self.company_id and self.company_id.dhl_spain_customer_number,
            "Receiver": {
                "Name": "%s" % receiver_id and receiver_id.name,
                "Address": "%s" % receiver_id and receiver_id.street,
                "City": "%s" % receiver_id and receiver_id.city,
                "PostalCode": "%s" % receiver_id and receiver_id.zip,
                "Country": "%s" % receiver_id and receiver_id.country_id and receiver_id.country_id.code,
                "Phone": "%s" % receiver_id and receiver_id.phone or receiver_id.mobile,
                "Email": "%s" % receiver_id and receiver_id.email
            },
            "Reference": "%s" % picking and picking.sale_id and picking.sale_id.client_order_ref or " ",
            "ServiceType": "%s" % self.dhl_spain_service_type,
            "Quantity": no_of_packages,
            "Weight": picking.shipping_weight/no_of_packages,
            "Incoterms": "%s" % self.dhl_spain_incoterm,
            "ContactName": "%s" % receiver_id.name,
            "GoodsDescription": "%s" % ', '.join(
                picking and picking.sale_id and picking.sale_id.order_line.mapped('product_id.name')),
            "Product": "%s" % self.dhl_spain_product,
            "Format": "PDF",
        }
        return request_data

    @api.model
    def dhl_spain_send_shipping(self, pickings):
        request_data = self.dhl_spain_prepare_body(picking=pickings)
        status, status_code, response = DHLSpainRequest.send_request(self.company_id, service='shipment', method='POST',
                                                                     data=json.dumps(request_data), param=False)
        if status:
            tracking = response and response.get('Tracking')
            label_data = response and response.get('Label')
            binary_data = binascii.a2b_base64(str(label_data))
            lp_number = response and response.get('LP')
            if isinstance(lp_number, list):
                lp_number = ', '.join(lp_number)
            pickings.dhl_lp_number = lp_number
            message = (
                _("Shipment created!<br/> <b>Label Number : </b>{0} <b>").format(tracking))
            pickings.message_post(body=message, attachments=[
                ('DHL-%s.%s' % (tracking, "pdf"), binary_data)])
            shipping_data = {
                'exact_price': 0.0,
                'tracking_number': tracking}
            return [shipping_data]
        else:
            raise ValidationError("%s \n %s" % (status_code, response))

    def dhl_spain_cancel_shipment(self, pickings):
        params = "?Year=0&Tracking=%s&Action=DELETE" % (pickings and pickings.carrier_tracking_ref)
        status, status_code, response = DHLSpainRequest.send_request(self.company_id, service='delete', method='GET',
                                                                     data=False, param=params)
        if not status:
            raise ValidationError("%s \n %s" % (status_code, response))

    def dhl_spain_get_tracking_link(self, pickings):
        return "https://clientesparcel.dhl.es/LiveTrackingN/"