import requests
import logging
from odoo import models, fields, api, _
from odoo.addons.mrw_shipping_integration_vts.models.mrw_response import Response
from odoo.exceptions import Warning, ValidationError, UserError
import xml.etree.ElementTree as etree
import re
_logger = logging.getLogger("MRW")


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("mrw_vts", "MRW")], ondelete={'mrw_vts': 'set default'})
    package_id = fields.Many2one('stock.package.type', string="package", help="please select package type")
    mrw_service_code = fields.Selection([('0000', '0000 - Urgent 10'),
                                         ('0005', '0005 - Urgent Today'),
                                         ('0010', '0010 - Promotions'),
                                         ('0100', '0100 - Urgent 12'),
                                         ('0110', '0110 - Urgent 14'),
                                         ('0200', '0200 - Urgent 19'),
                                         ('0205', '0205 - Urgent 19 Expedicion'),
                                         ('0210', '0210 - Urgent 19 Mas 40 Kilos'),
                                         ('0220', '0220 - 48 Hours Portugal'),
                                         ('0230', '0230 - Bag 19'),
                                         ('0235', '0235 - Bag 14'),
                                         ('0300', '0300 - Economic'),
                                         ('0310', '0310 - Economic +40Kg'),
                                         ('0350', '0350 - Economic Interinsular'),
                                         ('0400', '0400 - Document Express'),
                                         ('0450', '0450 - Express 2 Kg'),
                                         ('0480', '0480 - Express Box 3 Kg'),
                                         ('0490', '0490 - Documents 14'),
                                         ('0800', '0800 - Ecommerce'),
                                         ], default="", string="Mrw Service Code",
                                        help="service code given by Mrw.")

    def mrw_vts_rate_shipment(self, orders):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    @api.model
    def mrw_vts_send_shipping(self, pickings):
        """This Method Is Used For Send The Data To Shipper"""
        if self.prod_environment == False:
            label_url = "http://sagec-test.mrw.es/Panel.aspx"
            shipment_details = "http://sagec-test.mrw.es/panelseguimiento.aspx"
        else:
            label_url = "http://sagec.mrw.es/Panel.aspx"
            shipment_details = "http://sagec.mrw.es/panelseguimiento.aspx"
        response = []
        for picking in pickings:
            total_bulk_weight = picking.weight_bulk
            picking_partner_id = picking.partner_id
            picking_company_id = picking.picking_type_id.warehouse_id.partner_id
            shipment_request = etree.Element("soap:Envelope")
            shipment_request.attrib['xmlns:soap'] = 'http://www.w3.org/2003/05/soap-envelope'
            shipment_request.attrib['xmlns:mrw'] = "http://www.mrw.es/"
            header_node = etree.SubElement(shipment_request, "soap:Header")
            auth_info = etree.SubElement(header_node, 'mrw:AuthInfo')
            etree.SubElement(auth_info, 'mrw:CodigoFranquicia').text = str(
                self.company_id and self.company_id.mrw_agency_code)
            etree.SubElement(auth_info, 'mrw:CodigoAbonado').text = str(
                self.company_id and self.company_id.mrw_subscriber_code)
            etree.SubElement(auth_info, 'mrw:UserName').text = str(
                self.company_id and self.company_id.mrw_user_name)
            etree.SubElement(auth_info, 'mrw:Password').text = str(
                self.company_id and self.company_id.mrw_user_password)
            body_node = etree.SubElement(shipment_request, "soap:Body")
            TransmEnvio = etree.SubElement(body_node, "mrw:TransmEnvio")
            request = etree.SubElement(TransmEnvio, "mrw:request")
            data_collection = etree.SubElement(request, "mrw:DatosRecogida")
            sender_direction = etree.SubElement(data_collection, "mrw:Direccion")
            etree.SubElement(sender_direction, 'mrw:CodigoDireccion').text = "POSTMEDIA"
            etree.SubElement(sender_direction, 'mrw:Via').text = picking_company_id.street or ""
            etree.SubElement(sender_direction, 'mrw:Numero').text = picking_company_id.street2 or ""
            etree.SubElement(sender_direction, 'mrw:CodigoPostal').text = picking_company_id.zip or ""
            etree.SubElement(sender_direction, 'mrw:Poblacion').text = picking_company_id.city or ""
            etree.SubElement(data_collection, 'mrw:Nombre').text = picking_company_id.name or ""
            etree.SubElement(data_collection, 'mrw:Telefono').text = picking_company_id.phone or ""
            delivery_data = etree.SubElement(request, "mrw:DatosEntrega")
            receiver_direction = etree.SubElement(delivery_data, "mrw:Direccion")
            etree.SubElement(receiver_direction, 'mrw:Via').text = picking_partner_id.street or ""
            etree.SubElement(receiver_direction, 'mrw:Numero').text = re.search(r'\d{1,5}', picking_partner_id.street2).group() if any(map(str.isdigit, picking.partner_id.street2))  else ''#picking_partner_id.street2 or ""
            etree.SubElement(receiver_direction, 'mrw:CodigoPostal').text = picking_partner_id.zip or ""
            etree.SubElement(receiver_direction, 'mrw:Poblacion').text = picking_partner_id.city or ""
            etree.SubElement(delivery_data, 'mrw:Nombre').text = picking_partner_id.name or ""
            etree.SubElement(delivery_data, 'mrw:Telefono').text = picking_partner_id.phone or ""
            data_service = etree.SubElement(request, "mrw:DatosServicio")
            etree.SubElement(data_service, 'mrw:Fecha').text = picking.scheduled_date.strftime("%d-%m-%Y")
            etree.SubElement(data_service, 'mrw:Referencia').text = picking.origin or ""
            etree.SubElement(data_service, 'mrw:CodigoServicio').text = self.mrw_service_code
            Packages = etree.SubElement(data_service, "mrw:Bultos")
            number_of_packages = 0
            for package_id in pickings.package_ids:
                package_request = etree.SubElement(Packages, "mrw:BultoRequest")
                etree.SubElement(package_request,'mrw:Alto').text = "{}".format(package_id.package_type_id and package_id.package_type_id.height or 0)
                etree.SubElement(package_request,'mrw:Largo').text = "{}".format(package_id and package_id.package_type_id.packaging_length or 0)
                etree.SubElement(package_request,'mrw:Ancho').text = "{}".format(package_id and package_id.package_type_id.width or 0)
                etree.SubElement(package_request, 'mrw:Peso').text = "{}".format(int(package_id.shipping_weight))
                number_of_packages += 1
            if total_bulk_weight >0:
                package_request = etree.SubElement(Packages, "mrw:BultoRequest")
                etree.SubElement(package_request, 'mrw:Alto').text = "{}".format(
                    self.package_id and self.package_id.height or 0)
                etree.SubElement(package_request, 'mrw:Largo').text = "{}".format(
                    self.package_id and self.package_id.packaging_length or 0)
                etree.SubElement(package_request, 'mrw:Ancho').text = "{}".format(
                    self.package_id and self.package_id.width or 0)
                etree.SubElement(package_request, 'mrw:Peso').text = "{}".format(int(total_bulk_weight))
                number_of_packages += 1
            etree.SubElement(data_service, 'mrw:NumeroBultos').text = "{}".format(number_of_packages)
            etree.SubElement(data_service, 'mrw:Peso').text = "{}".format(int(picking.shipping_weight))
            etree.SubElement(data_service, 'mrw:NumeroPuentes').text = "{}".format(number_of_packages)
            try:
                headers = {
                    'Content-Type': 'application/soap+xml; charset=utf-8',
                    'Accept': 'application/soap+xml;charset=utf-8'}
                url = self.company_id and self.company_id.mrw_api_url
                _logger.info("Shipment Request Data:::: %s" % etree.tostring(shipment_request))
                response_data = requests.request(method="POST", url=url, headers=headers,
                                                 data=etree.tostring(shipment_request))
                api = Response(response_data)
                response_data = api.dict()
                _logger.info("Shipment Response Data:::%s" % response_data)
                TransmEnvioResult = response_data.get('Envelope', {}) and response_data.get('Envelope', {}).get('Body',{})\
                                    and response_data.get('Envelope', {}).get('Body', {}).get('TransmEnvioResponse', {}) \
                                    and response_data.get('Envelope', {}).get('Body', {}).get('TransmEnvioResponse',{}).get('TransmEnvioResult', {})\
                                    and response_data.get('Envelope', {}).get('Body',{}).get('TransmEnvioResponse', {}).get('TransmEnvioResult', {})
                if TransmEnvioResult.get('Estado') == '1':
                    picking.mrw_label_url = label_url + "?Franq=%s&Ab=%s&Dep=%s&Pwd=%s&Usr=%s&NumEnv=%s" % (
                        self.company_id.mrw_agency_code, self.company_id.mrw_subscriber_code, "",
                        self.company_id.mrw_user_password, self.company_id.mrw_user_name,
                        TransmEnvioResult.get('NumeroEnvio'))
                    picking.shipment_details = shipment_details + "?usuario=%s&pass=%s&albaran=%s" % (
                        self.company_id.mrw_user_name, self.company_id.mrw_user_password,
                        TransmEnvioResult.get('NumeroEnvio'))
                    if not picking.mrw_label_url:
                        raise ValidationError(
                            _("Shipment Url  Not Found In Response \n Response Data {}").format(response_data))
                    shipping_data = {'exact_price': 0.0, 'tracking_number': TransmEnvioResult.get('NumeroEnvio', {})}
                    response += [shipping_data]
                    return response
                else:
                    raise ValidationError(
                        _("Shipment Number Not Found In Response \n Response Data {}").format(response_data))
            except Exception as e:
                raise ValidationError(e)

    def mrw_vts_cancel_shipment(self, picking):
        """This Method is Used For Cancel The Order"""
        
        shipment_cancel_request = etree.Element("Envelope")
        shipment_cancel_request.attrib['xmlns'] = "http://schemas.xmlsoap.org/soap/envelope/"
        header_cancel_node = etree.SubElement(shipment_cancel_request, "Header")
        cancel_auth_info = etree.SubElement(header_cancel_node, 'AuthInfo')
        cancel_auth_info.attrib['xmlns'] = "http://www.mrw.es/"
        etree.SubElement(cancel_auth_info, 'CodigoFranquicia').text = str(
            self.company_id and self.company_id.mrw_agency_code)
        etree.SubElement(cancel_auth_info, 'CodigoAbonado').text = str(
            self.company_id and self.company_id.mrw_subscriber_code)
        etree.SubElement(cancel_auth_info, 'UserName').text = str(
            self.company_id and self.company_id.mrw_user_name)
        etree.SubElement(cancel_auth_info, 'Password').text = str(
            self.company_id and self.company_id.mrw_user_password)
        cancel_body_node = etree.SubElement(shipment_cancel_request, "Body")
        cancel_node = etree.SubElement(cancel_body_node, "CancelarEnvio")
        cancel_node.attrib['xmlns'] = "http://www.mrw.es/"
        cancel_request_node = etree.SubElement(cancel_node, "request")
        cancel_shipping_node = etree.SubElement(cancel_request_node, 'CancelaEnvio')
        etree.SubElement(cancel_shipping_node, 'NumeroEnvioOriginal').text = str(picking.carrier_tracking_ref)
        try:
            headers = {'Content-Type': 'text/xml; charset="utf-8','SOAPAction': '"http://www.mrw.es/CancelarEnvio"'}
            url = self.company_id and self.company_id.mrw_api_url
            _logger.info("Cancel Shipment Request Data ::::%s" % etree.tostring(shipment_cancel_request))
            response_data = requests.request(method="POST", url=url, headers=headers,data=etree.tostring(shipment_cancel_request))
            xml = Response(response_data)
            response_data = xml.dict()
            status_code = response_data.get('Envelope', {}) and response_data.get('Envelope', {}).get('Body', {}) and \
                          response_data.get('Envelope', {}).get('Body', {}).get('CancelarEnvioResponse', {}) and \
                          response_data.get('Envelope', {}).get('Body', {}).get('CancelarEnvioResponse', {}).get('CancelarEnvioResult', {}) and \
                          response_data.get('Envelope', {}).get('Body', {}).get('CancelarEnvioResponse', {}).get('CancelarEnvioResult', {}).get('Estado', {})
            _logger.info(status_code)
            if status_code == '1':
                return True
            else:
                raise ValidationError(_("Shipment Number Not Cancel  \n Response Data {}").format(response_data))
        except Exception as e:
            raise ValidationError(e)

    def mrw_vts_get_tracking_link(self, pickings):
        """This Method is Used For Tracking The Order"""
        return "https://www.mrw.es/seguimiento_envios/MRW_resultados_consultas.asp?modo=nacional&envio=%s" % (pickings.carrier_tracking_ref)
