# Monkey patching has to be done before importing anything else
# from gevent import monkey
# monkey.patch_all()

import atexit
import subprocess
import sys

import folium
from astra.global_tools import progress_vals_to_msg
from flask import Flask, copy_current_request_context, render_template, session, request
from flask_socketio import SocketIO, emit, disconnect
from find_launch_time.logic.find_time import make_launch_params, make_flight_params

from db import db
from simulations import run_sim


app = Flask(__name__)
db.init_app(app)
sio = SocketIO(app)





@app.route('/')
def index():
    m = folium.Map()
    # set the iframe width and height
    m.get_root().width = "100%"
    m.get_root().height = "100%"
    iframe = m.get_root()._repr_html_()
    return render_template('index.html', iframe=iframe, async_mode=sio.async_mode)


def run_sim_keep_client_updated_using_callback(sid: str):
    def simulation_progress_handler_factory(sid: str):
        def update_simulation_progress(progress: float, task: int):
            message_lines = progress_vals_to_msg(progress, task)
            for line in message_lines:
                sio.emit('sim_progress', {'data': line}, to=sid)

        return update_simulation_progress

    update_simulation_progress = simulation_progress_handler_factory(sid)
    run_sim(progress_handler=update_simulation_progress)


def run_sim_keep_client_updated_using_subprocess(sid: str):
    def update_progress(out, sid):
        sio.emit('sim_progress', {'data': out}, to=sid)

    p = subprocess.Popen(
        [sys.executable, 'simulations.py'], stdout=subprocess.PIPE, bufsize=1, text=True
    )
    for line in iter(p.stdout.readline, ''):
        if line.strip():
            update_progress(line, sid)
    p.stdout.close()


@sio.on('run_sim')
def run_sim_endpoint_0():
    if not hasattr(request, 'sid'):
        raise RuntimeError("No request.sid attribute found")
    sid = request.sid
    emit('sim_progress', {'data': 'Starting simulation'}, room=sid)
    run_sim_keep_client_updated_using_callback(sid)


if __name__ == '__main__':
    sio.run(app)
