# -*- coding: utf-8 -*-
from odoo.addons.seur_odoo_interation.model.seur_response import Response
from odoo.exceptions import ValidationError
import xml.etree.ElementTree as etree
from xml.sax.saxutils import unescape
from odoo import fields, models, api
import binascii
import requests
import logging

_logger = logging.getLogger("SEUR")


class SeurDeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[("seur", "Seur")], ondelete={'seur': 'set default'})

    clave_portes = fields.Selection([('F', 'F, Invoice Factura (Transport Charge Paid)'), ('D', 'D, Due (Debido)')],
                                    string="Label Type check for cold store")
    clave_pode = fields.Selection([('S', 'S, Seur (Return of SEUR delivery note  signed)'),
                                   ('I', 'I, Immediate (Return of signed sender documents)'),
                                   (" ", "Without CDE (Without Proof of delivery)")],
                                  string="Type Of Proof Of Delivery Of Used")

    clave_reembolso = fields.Selection([('F', "F, Factura (Invoice, The sender pays refund costs."),
                                        ("D", "D, Debido (Owed, The addressee pays the refund costs."),
                                        (" ", "No refund (There is no refund to be made.)")],
                                       string="Who Pays the refund payment?")
    type_of_route = fields.Selection([("AUT", "AUT, AUTOVIA"), ("AVD", "AVD, AVENIDA"),
                                      ("CL", "CL, CALLE"), ("CRT", "CRT, CARRETERA"),
                                      ("CTO", "CTO, CENTRO COMERCIAL"), ("EDF", "ED, EDIFICIO"),
                                      ("ENS", "ENS, ENSANCHE"), ("GTA", "GTA, GLORIETA"), ("GRV", "GRV, GRAN VIA"),
                                      ("PSO", "PSO, PASEO"), ("PZA", "PZA, PLAZA"), ("POL", "POL, POLIGONO INDUSTRIAL"),
                                      ("RAM", "RAM, RAMBLA"), ("RDA", "RDA, RONDA"), ("ROT", "ROT, ROTONDA"),
                                      ("TRV", "TRV,TRAVESIA"), ("URB", "URBANIZACION")], string="Type Of Route")
    type_of_number_of_route = fields.Selection([('N', "N, Número"), ("BL", "BL, Bloque"), ("IN", "IN, Indefinido"),
                                                ("KM", "Km, Kilómetro"), ("LT", "LT, Lote"), ("NV", "NV, Nave")],
                                               string="Type Of Number Of Route")

    seur_service_code = fields.Selection(
        [('1', '1, SEUR - 24'), ('3', '3, SEUR - 10'), ('5', '5, MISMO DIA'), ('7', '7, COURIER'),
         ('9', '9, SEUR 13:30'), ('13', '13, SEUR - 72'), ('15', '15, S-48'), ('17', '17, MARITIMO'),
         ('19', '19, NETEXPRESS'), ('77', '77, CLASSIC'), ('83', '83, SEUR 8:30')],
        string="Seru's Service Code")
    seur_product_code = fields.Selection([('2', '2, ESTANDARD (STANDARD)'), ('4', '4, MULTIPACK'),
                                          ('6', '6, MULTI BOX'), ('18', '18, FRIO (COLD)'),
                                          ('52', '52, MULTI DOC'), ('54', '54, DOCUMENTS'),
                                          ('70', '70, INTERNATIONAL T'),
                                          ('72', '72, INTERNATIONAL A'), ('76', '76, CLASSIC'),('104','104,PREDICT CROSSBORDER')],
                                         string="Seur's Product Code")

    def seur_rate_shipment(self, order):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def seur_cdata(self, text):
        element = etree.Element('<![CDATA[')
        element.text = text
        return element

    def seur_request_data(self, pickings):
        """
        :return this method return request data for seur label api
        """

        ci = self.company_id and self.company_id.seur_customer_integration_code
        nif = self.company_id and self.company_id.seur_tax_identifier_number
        ccc = self.company_id and self.company_id.seur_customer_code
        total_bultos = "1"  # number of packages
        peso_bultos = int(pickings.shipping_weight)  # total weight of parcel
        nombre_consignatario = pickings.partner_id  # the name of the Consignee.
        if not nombre_consignatario.zip and not nombre_consignatario.city and not nombre_consignatario.street and not nombre_consignatario.country_id:
            raise ValidationError("Please proper define receiver street, zip, city country")
        direccion_consignatario = nombre_consignatario.street  # the name of the Consignee’s address.
        country_code = nombre_consignatario and nombre_consignatario.country_id and nombre_consignatario.country_id.code
        cdata = """
        <![CDATA[<?xml version="1.0" encoding="utf-8"?><root><exp><bulto><ci>{0}</ci><nif>{1}</nif
        ><ccc>{2}</ccc><servicio>{3}</servicio><producto>{4}</producto><total_bultos>{5}</total_bultos><pesoBulto>{6}</pesoBulto><referencia_expedicion>{7}
        </referencia_expedicion><clavePortes>{8}</clavePortes><clavePod>{9}</clavePod
        ><claveReembolso>{10}</claveReembolso><nombre_consignatario>{11}</nombre_consignatario><direccion_consignatario>{12} 
        </direccion_consignatario><tipoVia_consignatario>{13}
        </tipoVia_consignatario><tNumVia_consignatario>{14}</tNumVia_consignatario><poblacion_consignatario>{15}
        </poblacion_consignatario><codPostal_consignatario>{16}</codPostal_consignatario><pais_consignatario>{17}
        </pais_consignatario><email_consignatario>{18}</email_consignatario><telefono_consignatario>{19}</telefono_consignatario></bulto></exp></root>]]> """.format(ci, nif, ccc, self.seur_service_code,
                                                                 self.seur_product_code, total_bultos, peso_bultos,
                                                                 pickings.sale_id.name,
                                                                 self.clave_portes, self.clave_pode,
                                                                 self.clave_reembolso, nombre_consignatario.name,
                                                                 direccion_consignatario,
                                                                 self.type_of_route, self.type_of_number_of_route,
                                                                 nombre_consignatario.city, nombre_consignatario.zip,
                                                                 country_code,nombre_consignatario.email,nombre_consignatario.phone)

        root_node_envelope = etree.Element("soapenv:Envelope")
        root_node_envelope.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
        root_node_envelope.attrib['xmlns:imp'] = "http://localhost:7026/ImprimirECBWebService"
        root_node_header = etree.SubElement(root_node_envelope, 'soapenv:Header/')
        root_node_body = etree.SubElement(root_node_header, 'soapenv:Body')
        root_node_imp = etree.SubElement(root_node_body, 'impresionIntegracionPDFConECBWS')
        etree.SubElement(root_node_imp, 'in0').text = self.company_id and self.company_id.seur_username
        etree.SubElement(root_node_imp, 'in1').text = self.company_id and self.company_id.seur_password
        in2 = etree.SubElement(root_node_imp, 'in2')
        in2.text = cdata
        etree.SubElement(root_node_imp, 'in3').text = "comunicacion.xml"
        etree.SubElement(root_node_imp, 'in4').text = self.company_id and self.company_id.seur_tax_identifier_number
        etree.SubElement(root_node_imp, 'in5').text = self.company_id and self.company_id.seur_franchise_code
        etree.SubElement(root_node_imp, 'in6').text = self.company_id and self.company_id.seur_account_code
        etree.SubElement(root_node_imp, 'in7').text = ""
        _logger.info("XML Request%s"%etree.tostring(root_node_envelope))
        return unescape(etree.tostring(root_node_envelope).decode())

    @api.model
    def seur_send_shipping(self, pickings):
        request_data = self.seur_request_data(pickings)
        _logger.info("Shipment Request Data %s" % request_data)
        url = "{}/CIT-war/services/ImprimirECBWebService".format(self.company_id and self.company_id.seur_api_url)
        try:
            headers = {
                'Content-Type': 'text/xml; charset="utf-8'

            }
            _logger.info(">>>>> Sending POST Request to {}".format(url))
            _logger.info(">>>> Request Data {}".format(request_data))
            response_data = requests.post(url=url, data=request_data, headers=headers)
        except Exception as error:
            raise ValidationError(error)
        if response_data.status_code in [200, 201]:
            _logger.info("Successfully Response From {0} \n Response Data".format(url, response_data))
            response_data = Response(response_data)
            response_data = response_data.dict()
            ecb_number = response_data.get('Envelope') and response_data.get('Envelope').get('Body') \
                         and response_data.get('Envelope').get('Body').get('impresionIntegracionPDFConECBWSResponse') \
                         and response_data.get('Envelope').get('Body').get(
                'impresionIntegracionPDFConECBWSResponse').get(
                'out') \
                         and response_data.get('Envelope').get('Body').get(
                'impresionIntegracionPDFConECBWSResponse').get(
                'out').get('ECB') \
                         and response_data.get('Envelope').get('Body').get(
                'impresionIntegracionPDFConECBWSResponse').get(
                'out').get('ECB').get('string') \
                         and response_data.get('Envelope').get('Body').get(
                'impresionIntegracionPDFConECBWSResponse').get(
                'out').get('ECB').get('string')
            label_data = response_data.get('Envelope') and response_data.get('Envelope').get('Body') \
                         and response_data.get('Envelope').get('Body').get(
                'impresionIntegracionPDFConECBWSResponse') and \
                         response_data.get('Envelope').get('Body').get('impresionIntegracionPDFConECBWSResponse').get(
                             'out') \
                         and response_data.get('Envelope').get('Body').get(
                'impresionIntegracionPDFConECBWSResponse').get('out').get('PDF')
            if not ecb_number and label_data:
                raise ValidationError("Label Data not found in response \n".format(response_data))
            label_data = binascii.a2b_base64(str(label_data))
            log_msg = "<b>ECB Numbers:</b> %s" % ecb_number
            pickings.message_post(body=log_msg,
                                  attachments=[("SEUR %s.pdf" % (ecb_number), label_data)])
            shipping_data = {'exact_price': 0.0, 'tracking_number': ecb_number}
            response = []
            response += [shipping_data]
            return response
        else:
            raise ValidationError(response_data)

    def seur_cancel_shipment(self, picking):
        raise ValidationError("Cancel Service does not provide by SEUR")

    def seur_get_tracking_link(self, picking):
        """This Method Is Used For Track The Shipment"""
        return "https://www.seur.com/livetracking/"
