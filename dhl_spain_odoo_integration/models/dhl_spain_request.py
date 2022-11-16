from requests import request
import logging

_logger = logging.getLogger("DHL Spain")


def _prepare_dhl_api_url(hostname, service):
    """
    :service: api service provide by DHL
    """
    if service == 'shipment':
        return "%s/cimapi/api/v1/customer/shipment" % hostname
    elif service == 'authentication':
        return "%s/cimapi/api/v1/customer/authenticate" % hostname
    elif service == 'delete':
        return "%s/cimapi/api/v1/customer/shipment" % hostname


def check_required_value(required_param, odoo_object):
    """
    :param required_param: require filed list
    :param odoo_object: odoo object
    """
    missing_field = [odoo_object[param] for param in required_param if not odoo_object[param]]
    return missing_field


class DHLSpainRequest():

    def send_request(self, service, method, data, param):
        """
        :param service: api service provide by DHL
        :param method: DHL API service method like POST, GET
        :param data: Request body data
        """
        api_url = _prepare_dhl_api_url(self.dhl_spain_url, service=service)
        headers = {
            'Content-Type': 'application/json',
        }
        if service == 'delete':
            api_url = api_url + param
        _logger.info("[SEND] %s To %s" % (method, api_url))
        _logger.info("[REQUEST BODY] %s" % data)
        if service != 'authentication':
            headers.update({'Authorization': 'Bearer {}'.format(self.dhl_spain_token)})
        try:
            response = request(method=method, url=api_url, data=data, headers=headers)
        except Exception as error:
            _logger.error(error)
            return False, False, error
        if response.status_code in [200, 201]:
            _logger.info('[SUCCESS] %s' % response)
            return True, response.status_code, response.json()
        else:
            _logger.info('[FAIL] %s' % response)
            return False, response.status_code, response.text
