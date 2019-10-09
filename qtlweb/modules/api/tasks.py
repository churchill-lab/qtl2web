# -*- coding: utf-8 -*-
import time
import requests
import json

from qtlweb.app import create_celery_app
from qtlweb.utils import format_time

celery = create_celery_app()


@celery.task(bind=True, ignore_result=True)
def call_api(self, url_id, url):
    """Celery task to call the url's and get back the data.

    Args:
        self: Celery reference
        url_id (str): identifier of url
        url (str): url to call

    Returns:
        dict: a dictionary specifying the state and results
    """
    meta = {'url_id': url_id, 'url': url}
    # print('call_api: meta = ', meta)

    self.update_state(state='PROGRESS', meta=meta)

    try:
        request_start_time = time.time()

        r = requests.get(url)

        request_end_time = time.time()
        roundtrip = r.elapsed.total_seconds()
        request_time = format_time(0, roundtrip)
        transfer_time = format_time(request_start_time + roundtrip,
                                    request_end_time)
        total_time = format_time(request_start_time, request_end_time)

        response_data = json.loads(r.content.decode("utf-8"))
        #response_data = r.content

        meta['response'] = response_data
        meta['time_request'] = request_time
        meta['time_transfer'] = transfer_time
        meta['time_total'] = total_time
        meta['from_cache'] = r.from_cache
        meta['status_code'] = r.status_code

    except requests.exceptions.ConnectionError as req_exc_connect:
        print('ConnectionError in call_api task: ', str(req_exc_connect))
        meta['error'] = 'Connection Error'
        meta['error_message'] = str(req_exc_connect)
    except requests.exceptions.HTTPError as req_exc_http:
        print('HTTPError in call_api task: ', str(req_exc_http))
        meta['error'] = 'HTTP Error'
        meta['error_message'] = str(req_exc_http)
    except requests.exceptions.Timeout as req_exc_timeout:
        print('Timeout in call_api task: ', str(req_exc_timeout))
        meta['error'] = 'Timeout Error'
        meta['error_message'] = str(req_exc_timeout)
    except requests.exceptions.RequestException as req_exc:
        print('RequestException in call_api task: ', str(req_exc))
        meta['error'] = 'Request Error'
        meta['error_message'] = str(req_exc)
    except Exception as e:
        print('Exception in call_api task: ', str(e))
        meta['error'] = 'Error'
        meta['error_message'] = str(e)

    # Initial implementation had state='FAILURE', but ran into several issues.
    #
    # store_errors_even_if_ignored=True (IF using 'FAILURE' state)
    #
    # Essentially the task is completing even on request errors, it's just
    # getting bad responses from the request.
    #
    # Instead of FAILURE, we will set SUCCESS and handle it on the client side.

    self.update_state(state='SUCCESS', meta=meta)

    return None



