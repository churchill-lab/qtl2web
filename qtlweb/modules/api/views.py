# -*- coding: utf-8 -*-
from celery import group, current_app

from flask import current_app as app
from flask import Blueprint
from flask import jsonify
from flask import request

import json
import time
import requests

from qtlweb.utils import format_time

api = Blueprint('api', __name__, template_folder='templates', url_prefix='/api')


def split_url(url):
    """Splits the given URL into a tuple of (protocol, host, uri)"""
    proto, rest = url.split(':', 1)
    rest = rest[2:].split('/', 1)
    host, uri = (rest[0], rest[1]) if len(rest) == 2 else (rest[0], "")
    return proto, host, uri


def parse_url(url):
    """Parses out Referer info indicating the request is from a previously proxied page.
    For example, if:
        Referer: http://localhost:8080/proxy/google.com/search?q=foo
    then the result is:
        ("google.com", "search?q=foo")
    """
    proto, host, uri = split_url(url)

    #print('url=', url)
    #print('proto=', proto)
    #print('host=', host)
    #print('uri=', uri)

    if uri.find("/") < 0:
        return None

    rest = uri.split("/", 2)[2]

    return {'proto': proto, 'host': host, 'uri': uri, 'url': rest}


class Cache:
    def __init__(self):
        self.urls = {}


CACHE = Cache()


@api.route('/get/<path:url>', methods=['GET'])
def api_get(url):
    request_start_time = time.time()
    print('request.url=', request.url)
    print('param url=', url)

    elems = request.url.split(url)

    if len(elems) > 1:
        new_url = '{}{}'.format(url, elems[1])
    else:
        new_url = url

    print('new_url=', new_url)

    r = requests.get(new_url)  # , params=_params)
    request_end_time = time.time()
    roundtrip = r.elapsed.total_seconds()
    request_time = format_time(0, roundtrip)
    transfer_time = format_time(request_start_time + roundtrip, request_end_time)
    total_time = format_time(request_start_time, request_end_time)

    response_data = r.content
    try:
        response_data = json.loads(r.content.decode("utf-8"))
    except Exception as e:
        print('Error in JSON: ', str(e))

    return jsonify(response_data)


@api.route('/submit', methods=['POST'])
def api_submit():
    from qtlweb.modules.api.tasks import call_api

    json_data = request.get_json()
    urls = json_data['urls']

    print('submit called with: ', urls)

    calls = []
    for i, url_info in enumerate(urls):
        calls.append(call_api.s(url_info['url_id'], url_info['url']))

    # create a group
    # class 'celery.canvas.group'
    job = group(calls)

    # call it
    # class 'celery.result.GroupResult'>
    result = job.apply_async()

    # save the result to get in next request
    result.save()

    return jsonify({'group_id': result.id})


@api.route('/status/<group_id>')
def api_status(group_id):
    """
    Query Celery for group status based on its taskid for a group

    Celery status can be one of:
    PENDING - Job not yet run or unknown status
    PROGRESS - Job is currently running
    SUCCESS - Job completed successfully
    FAILURE - Job failed
    REVOKED - Job get cancelled
    """
    print('status called for: ', group_id)
    from qtlweb.modules.api.tasks import celery

    # there is a rare occasion when an exception would be raised
    # code was added to make 5 attempts to enable more robust or
    # better fail-safe for calls made to get the status

    attempts = 5
    done = False

    while not done:

        try:
            # get the GroupResult
            rs = celery.GroupResult.restore(group_id)
            from qtlweb.modules.api.tasks import call_api

            if rs.ready():
                results = rs.get(propagate=False)

                data = {}
                error_count = 0
                for idx, res in enumerate(results):
                    if 'error' in res:
                        error_count += 1
                    data[res['url_id']] = res

                response_data = {
                    'task_id': group_id,
                    'status': 'DONE',
                    'number_tasks_submitted': len(rs.results),
                    'number_tasks_completed': rs.completed_count(),
                    'number_tasks_errors': error_count,
                    'response_data': data
                }

                # delete all the task_ids for this group_id from redis
                rs.forget()

                # group_id still exists, delete it from redis
                rs.delete()

            else:
                response_data = {
                    'task_id': group_id,
                    'status': 'RUNNING',
                    'number_tasks_submitted': len(rs.results),
                    'number_tasks_completed': rs.completed_count(),
                    'response_data': ''
                }

            done = True

        except Exception as exc:
            print('Major Error: ', str(exc))
            attempts -= 1
            if attempts <= 0:
                done = True

            response_data = {
                'task_id': group_id,
                'status': 'DONE',
                'error': 'UNKNOWN ERROR'
            }


    # TODO: loop through results and app to CACHE
    '''
    if task.state == 'SUCCESS':
        if response['url'] in CACHE.urls:
            CACHE.urls[response['url']]['hits'] += 1
        else:
            CACHE.urls[response['url']] = {'hits': 1}

        CACHE.urls[response['url']]['last'] = datetime.now()
    '''

    return jsonify(response_data)


@api.route('/status/task/<task_id>')
def api_status_task(task_id):
    """
    Query Celery for task status based on its taskid/jobid

    Celery status can be one of:
    PENDING - Job not yet run or unknown status
    PROGRESS - Job is currently running
    SUCCESS - Job completed successfully
    FAILURE - Job failed
    REVOKED - Job get cancelled
    """
    from qtlweb.modules.api.tasks import call_api
    task = call_api.AsyncResult(task_id)
    print(task)

    if task.ready():
        print(task.info)
    else:
        print('not ready')

    return jsonify({})


@api.route('/cancel/<group_id>')
def api_cancel(group_id):
    """
    Cancel Celery task
    REVOKED - Job gets cancelled
    """
    # TODO: this is now group id and not a single task_id, make sure this works
    try:
        rs = current_app.GroupResult.restore(group_id)
        rs.revoke(terminate=True)
    except Exception as exc:
        print('Major Error: ', str(exc))
    return jsonify({'status': 'revoked?'})


@api.route('/cancel/task/<task_id>')
def api_cancel_task(task_id):
    """
    Cancel Celery task
    REVOKED - Job get cancelled
    """
    from qtlweb.modules.api.tasks import celery, call_api
    task = call_api.AsyncResult(task_id)
    task.revoke(terminate=True)
    return jsonify({'status': task.state})


@api.route('/qtlapi/<path:url>')
def qtlapi(url):
    url_base = app.config['API_R_BASE']
    elems = request.url.split(url)

    if len(elems) > 1:
        url_api = f'{url_base}/{url}{elems[1]}'
    else:
        url_api = f'{url_base}/{url}'

    app.logger.info('API call: %s', url_api)

    #time_request_start = time.time()

    r = requests.get(url_api)

    #time_request_end = time.time()
    #roundtrip = r.elapsed.total_seconds()
    #time_request = format_time(0, roundtrip)
    #time_transfer = format_time(time_request_start + roundtrip,
    #                            time_request_end)
    #time_total = format_time(time_request_start, time_request_end)

    #app.logger.info(f'time_request={time_request}')
    #app.logger.info(f'time_transfer={time_transfer}')
    #app.logger.info(f'time_total={time_total}')
    #app.logger.info(f'from_cache={r.from_cache}')
    #app.logger.info(f'status_code={r.status_code}')

    #print(r.headers)

    return r.content
