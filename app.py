#!/usr/bin/env python3
from __future__ import absolute_import

import os
from time import time, strftime

from flask import Flask, jsonify, request, render_template, Response

from api_common import get_device_builds, get_oems, get_device_data
from changelog.gerrit import GerritJSONProvider
from custom_exceptions import DeviceNotFoundException, UpstreamApiException
from config import Config
from api_v1 import api as api_v1
from api_v2 import api as api_v2

import extensions

app = Flask(__name__)
app.config.from_object('config.FlaskConfig')
app.register_blueprint(api_v1, url_prefix='/api/v1')
app.register_blueprint(api_v2, url_prefix='/api/v2')
app.json = GerritJSONProvider(app)
app.url_map.strict_slashes = False
extensions.setup(app)


##########################
# Jinja2 globals
##########################

def version():
    return os.environ.get('VERSION', 'dev')[:6]


app.jinja_env.globals.update(version=version)


##########################
# Exception Handling
##########################

@app.errorhandler(DeviceNotFoundException)
def handle_unknown_device(error):
    if request.path.startswith('/api/'):
        return jsonify({'response': []})
    oems = get_oems()
    return render_template('error.html', header='Whoops - this page doesn\'t exist', message=error.message,
                           oems=oems), error.status_code


@app.errorhandler(UpstreamApiException)
def handle_upstream_exception(error):
    if request.path.startswith('/api/'):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    return render_template('error.html', header='Something went wrong', message=error.message,
                           oems={}), error.status_code


##########################
# Web Views
##########################

@app.context_processor
def inject_year():
    return dict(year=strftime('%Y'))


@app.route('/')
@extensions.cache.cached()
def show_index():
    oems = get_oems()

    return render_template('changes.html', oems=oems,
                           before=0, changelog=True)


@app.route('/<string:device>')
@extensions.cache.cached()
def web_device(device):
    oems = get_oems()
    device_data = get_device_data(device)
    roms = get_device_builds(device)

    for rom in roms:
        if device_data.get('lineage_recovery', True):
            # Pick recovery.img if exists, otherwise boot.img or None
            if recovery := next((x for x in rom['files'] if x['filename'] == 'recovery.img'), None) or \
                    next((x for x in rom['files'] if x['filename'] == 'boot.img'), None):
                rom['recovery'] = recovery

        rom['filename'] = rom['files'][0]['filename']
        rom['filepath'] = rom['files'][0]['filepath']
        rom['size'] = rom['files'][0]['size']

    has_recovery = any([True for rom in roms if 'recovery' in rom])

    return render_template('device.html', oems=oems, active_device_data=device_data,
                           roms=roms, has_recovery=has_recovery,
                           wiki_info=Config.WIKI_INFO_URL, wiki_install=Config.WIKI_INSTALL_URL,
                           download_base_url=Config.DOWNLOAD_BASE_URL)


@app.route('/<string:device>/changes')
@extensions.cache.cached()
def show_changelog(device):
    oems = get_oems()
    device_data = get_device_data(device)

    return render_template('changes.html', oems=oems, active_device_data=device_data,
                           before=0, changelog=True)



@app.route('/favicon.ico')
def favicon():
    return ''
