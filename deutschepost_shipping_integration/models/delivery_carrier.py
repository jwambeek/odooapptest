import logging
import json
from requests import request
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger("Deutschpost")


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("deutschepost", "Deutschepost")],
                                     ondelete={'deutschepost': 'set default'})
    customer_ekp_number = fields.Char(string="EKP Number",
                                      help="The customers ekp for whom the item shall be created.", copy=False)
    deutschepost_product = fields.Selection(
        [('GPP', 'GPP - Packet Plus'),
         ('GMP', 'GMP - Packet'),
         ('GMM', 'GMM - Business Mail Standard'),
         ('GMR', 'GMR - Business Mail Registered'),
         ('GPT', 'GPT - Packet Tracked')], default="GPP", string='Deutschepost Product')
    deutschepost_servicelevel = fields.Selection(
        [('PRIORITY', 'PRIORITY'),
         ('STANDARD', 'STANDARD'),
         ('REGISTERED', 'REGISTERED')], default="PRIORITY", string='Deutschepost Service Level',
        help="Registered is only available with product GMR and SalesChannel DPI, STANDARD is only available with products GMM and GMP, PRIORITY is only available with products GPT, GPP and GMP")

    deutschepost_pickuptimeslot = fields.Selection(
        [('MORNING', 'MORNING'),
         ('MIDDAY', 'MIDDAY'),
         ('EVENING', 'EVENING')], default="MIDDAY",
        string='Deutschepost Pickuptimeslot')

    deutschepost_pickup_type = fields.Selection(
        [('CUSTOMER_DROP_OFF', 'CUSTOMER_DROP_OFF'),
         ('SCHEDULED', 'SCHEDULED'),
         ('DHL_GLOBAL_MAIL', 'DHL_GLOBAL_MAIL'),
         ('adult_signature', 'adult_signature'),
         ('DHL_EXPRESS', 'DHL_EXPRESS')], default="CUSTOMER_DROP_OFF",
        string='Deutschepost Pickup Type')

    deutschepost_shipment_nature_type = fields.Selection(
        [('SALE_GOODS', 'SALE_GOODS'),
         ('RETURN_GOODS', 'RETURN_GOODS'),
         ('GIFT', 'GIFT'),
         ('COMMERCIAL_SAMPLE', 'COMMERCIAL_SAMPLE'),
         ('DOCUMENTS', 'DOCUMENTS'),
         ('MIXED_CONTENTS', 'MIXED_CONTENTS'),
         ('OTHERS', 'OTHERS')], default="OTHERS",
        string='Shipment Nature Type')

    deutschepost_packaging_id = fields.Many2one('stock.package.type', string="Default Package Type")

    def convert_weight(self, shipping_weight):
        grams_for_kg = 1000  # 1 Kg to Grams
        uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        if uom_id.name == 'kg':
            return str(int(round(shipping_weight * grams_for_kg, 3)))
        else:
            return str(int(shipping_weight))

    def deutschepost_rate_shipment(self, orders):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def deutschepost_order_request_data(self, picking):
        receipient_address = picking.partner_id
        sender_id = picking.picking_type_id and picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.partner_id
        package_details = picking.package_ids
        total_bulk_weight = picking.weight_bulk
        date_order = picking.scheduled_date
        package_data = []
        no_of_packages = (len(picking.package_ids) + (1 if picking.weight_bulk else 0))

        for package_id in package_details:
            package_data.append({
                "product": self.deutschepost_product,
                "serviceLevel": self.deutschepost_servicelevel,
                "recipient": receipient_address.name or '',
                "addressLine1": receipient_address.street or '',
                "city": receipient_address.city or '',
                "destinationCountry": receipient_address.country_id and receipient_address.country_id.code or '',
                "id": "",
                "custRef": "",
                "recipientPhone": "%s" % receipient_address.phone or "",
                "recipientFax": "",
                "recipientEmail": "%s" % (receipient_address.email or ''),
                "addressLine2": "%s" % (receipient_address.street2 or ''),
                "addressLine3": "",
                "state": receipient_address.state_id and receipient_address.state_id.code or '',
                "postalCode": "%s" % (receipient_address.zip or ''),
                "shipmentAmount": "%s" % (picking.sale_id and picking.sale_id.amount_total or ''),
                "shipmentCurrency": "EUR",
                "shipmentGrossWeight": self.convert_weight(package_id.shipping_weight),
                "returnItemWanted": False,
                "shipmentNaturetype": self.deutschepost_shipment_nature_type,
                "contents": [
                    {
                        "contentPieceAmount": '1',
                        "contentPieceDescription": package_id.name or '',
                        "contentPieceHsCode": "",
                        "contentPieceNetweight": self.convert_weight(package_id.shipping_weight),
                        "contentPieceOrigin": sender_id.country_id and sender_id.country_id.code or '',
                        "contentPieceValue": "%.2f" % (picking.sale_id.amount_total / no_of_packages)
                    }
                ]
            })
        if total_bulk_weight:
            package_data.append({
                "product": self.deutschepost_product,
                "serviceLevel": self.deutschepost_servicelevel,
                "recipient": receipient_address.name or '',
                "addressLine1": receipient_address.street or '',
                "city": receipient_address.city or '',
                "destinationCountry": receipient_address.country_id and receipient_address.country_id.code or '',
                "id": "",
                "custRef": "",
                "recipientPhone": "%s" % receipient_address.phone or "",
                "recipientFax": "",
                "recipientEmail": "%s" % (receipient_address.email or ''),
                "addressLine2": "%s" % (receipient_address.street2 or ''),
                "addressLine3": "",
                "state": receipient_address.state_id and receipient_address.state_id.code or '',
                "postalCode": "%s" % (receipient_address.zip or ''),
                "shipmentAmount": "%s" % (picking.sale_id and picking.sale_id.amount_total or ''),
                "shipmentCurrency": "EUR",
                "shipmentGrossWeight": self.convert_weight(total_bulk_weight),
                "returnItemWanted": False,
                "shipmentNaturetype": self.deutschepost_shipment_nature_type,
                "contents": [
                    {
                        "contentPieceAmount": '1',
                        "contentPieceDescription": picking.name or '',
                        "contentPieceHsCode": "",
                        "contentPieceNetweight": self.convert_weight(total_bulk_weight),
                        "contentPieceOrigin": sender_id.country_id and sender_id.country_id.code or '',
                        "contentPieceValue": "%.2f" % (picking.sale_id.amount_total / no_of_packages)
                    }
                ]
            })

        return {
            "customerEkp": "%s" % (self.customer_ekp_number),
            "orderStatus": "FINALIZE",
            "paperwork": {
                "contactName": "%s" % sender_id.name or '',
                "awbCopyCount": 1,
                "jobReference": "",
                "pickupType": self.deutschepost_pickup_type,
                "pickupLocation": "%s" % (sender_id.city or ""),
                "pickupDate": "{}".format(picking.scheduled_date.strftime("%Y-%m-%d")),
                "pickupTimeSlot": "%s" % (self.deutschepost_pickuptimeslot),
                "telephoneNumber": "%s" % (sender_id.phone or "")
            },
            "items": package_data
        }

    @api.model
    def deutschepost_send_shipping(self, pickings):
        for picking in pickings:
            try:
                request_data = self.deutschepost_order_request_data(picking)
                _logger.info("Shiping RequestData ::: %s" % request_data)
                api_url = "%s/dpi/shipping/v1/orders" % (self.company_id and self.company_id.deutschepost_api_url)
                headers = {"Accept": "application/json",
                           "Authorization": self.company_id.deutschepost_accesstoken,
                           "Content-Type": "application/json"}
                response_data = request(method='POST', url=api_url, data=json.dumps(request_data), headers=headers)
                _logger.info("Shipping Response ::::%s"%response_data.content)
                if response_data.status_code in [200, 201]:
                    responses = response_data.json()
                    _logger.info("Json Shipping Response ::::%s"%responses)
                    if not responses.get('orderId'):
                        raise ValidationError(responses)
                    picking.deutschpost_order_number = responses.get('orderId')
                    tracking_numbers = []
                    item_id_ls = []
                    for shipment in responses.get('shipments'):
                        tracking_numbers.append(shipment.get('awb'))
                        for item in shipment.get('items'):
                            item_id_ls.append(str(item.get('id')))
                    picking.deutschpost_item_id = ','.join(item_id_ls)
                    try:
                        for item_id in item_id_ls:
                            self.deutschpost_generate_label(item_id, pickings)
                    except Exception as e:
                        pickings.message_post(body=e)
                    return [{'exact_price': 0.0, 'tracking_number': ','.join(tracking_numbers)}]
                else:
                    raise ValidationError("Response : %s" % (response_data.content))
            except Exception as e:
                raise ValidationError(_("\n Response Data : %s") % (e))

    def deutschpost_generate_label(self, item_id, pickings):
        api_url = "{0}/dpi/shipping/v1/items/{1}/label".format(self.company_id.deutschepost_api_url, item_id)
        headers = {
            "Authorization": self.company_id.deutschepost_accesstoken,
            "Content-Type": "application/json"}
        try:
            response_data = request(method='GET', url=api_url, headers=headers)
            if response_data.status_code == 200:
                logmessage = ("<b>Label Generated:</b>")
                pickings.message_post(body=logmessage,
                                      attachments=[("%s.pdf" % (item_id), response_data.content)])
                return True
            else:
                raise ValidationError(response_data.content)
        except Exception as e:
            raise ValidationError(e)

    def deutschepost_cancel_shipment(self, picking):
        raise ValidationError("Please contact : support@vrajatechnologies.com")

    def deutschepost_get_tracking_link(self, picking):
        """This Method Is Used For Tracking Order"""
        return "https://www.dhl.com/de-en/home/tracking/tracking-express.html?submit=1&tracking-id={0}".format(
            picking.carrier_tracking_ref)
