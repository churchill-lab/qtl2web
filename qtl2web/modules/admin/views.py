# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import session
from flask import url_for


from qtl2web import utils

import ntpath
import os
import socket


admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.route('/')
def index():
    # POST search_term = request.form.get("search_term")
    # GET  search_term = request.args.get("search_term")
    # BOTH search_term = request.values.get("search_term")

    search_term = request.values.get('search_term', '')
    datasetid = request.values.get('datasetid', '')
    debug = utils.str2bool(request.values.get('debug', ''))

    app_version = os.getenv('DOCKER_QTL2WEB_VERSION', '')

    return render_template('admin/index.html',
                           search_term=search_term, datasetid=datasetid,
                           debug=debug, app_version=app_version)



