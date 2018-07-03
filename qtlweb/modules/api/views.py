from flask import (
    Blueprint,
    redirect,
    jsonify,
    request,
    url_for,
    Response,
    render_template)
from datetime import datetime
import time
import requests
from qtlweb.utils import format_time
import json
from celery import group, current_app
from celery.result import GroupResult
# INSTALL CACHE
#import requests_cache
#requests_cache.install_cache()

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

    print('url=', url)
    print('proto=', proto)
    print('host=', host)
    print('uri=', uri)

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



    #current_app.g.error(
    #    "[REQUEST] ['{}'] [{}] [{}] [{}]".format(request.url, request_time,
    #                                             transfer_time, total_time))

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

    #print('type(job)=', type(job))
    #print('type(result)=', type(result))

    # save the result to get in next request
    result.save()

    #print(result)

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
    try:
        # get the GroupResult
        # celery.result.GroupResult
        rs = celery.GroupResult.restore(group_id)
        #rs = current_app.GroupResult.restore(group_id)
        from qtlweb.modules.api.tasks import call_api
        print('rs=', rs)
        print(type(rs))


        #print('ready()=', rs.ready())
        #print('waiting()=', rs.waiting())
        #print('successful()=', rs.successful())
        #print('failed()=', rs.failed())

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

            for c in rs.children:
                c.get()
                c.forget()

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
    except Exception as exc:
        print('Major Error: ', str(exc))
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
    rs = current_app.GroupResult.restore(group_id)
    rs.revoke(terminate=True)
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


