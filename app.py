from gevent import monkey
monkey.patch_all()

import logging
import subprocess
import sys
from time import sleep

from flask import Flask, copy_current_request_context, render_template, session, request
from flask_socketio import SocketIO, emit, disconnect

from astra.global_tools import progress_vals_to_msg
from simulations import run_sim

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret'
sio = SocketIO(app)
logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)


@app.route('/')
def index():
    return render_template('index.html', async_mode=sio.async_mode)


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
    p = subprocess.Popen([sys.executable, 'simulations.py'], stdout=subprocess.PIPE, bufsize=1, text=True)
    for line in iter(p.stdout.readline, ""):
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


@sio.on('my_event')
def received_my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@sio.on('my_broadcast_event')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@sio.on('disconnect_request')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


if __name__ == '__main__':
    sio.run(app, debug=True)


