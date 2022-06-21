"""Fleet manager server

This server enables a centralized way of handling docker containers across multiple devices.
The server also tracks container versions and if there is newer versions available.

This server also comes with a wasy web app which visualizes the fleet.

This server also enables some commands for the user, such as update, start and stop.
"""

from logging import getLogger
import os
import sys
from http import HTTPStatus
from requests import post, get as http_get
from flask import Flask, request, render_template, Response, jsonify
from flask_socketio import SocketIO
from decentralized_logger import setup_logging, disable_loggers, level_translator
from docker_hub import DockerHub

# Feature flags
DEVELOPMENT_MODE = os.getenv("ENV", "").lower() == "development"

if DEVELOPMENT_MODE:
    parent_path = os.path.dirname(os.getcwd())
    sys.path.append(parent_path)

from fleet import Fleet                 # pylint: disable=wrong-import-position
import shared
from device_information import DeviceInformation

# Constants
APPLICATION_NAME = "fleet-manager-server"
APP_PORT = 5000

if DEVELOPMENT_MODE:
    APP_PORT = 5010

# Mandatory application settings
DOCKER_HUB_USERNAME = os.getenv("DOCKER_HUB_USERNAME")
DOCKER_HUB_PASSWORD = os.getenv("DOCKER_HUB_PASSWORD")
DOCKER_HUB_REPO = os.getenv("DOCKER_HUB_REPO")

# Checking application settings
if DOCKER_HUB_USERNAME is None:
    raise AttributeError('Missing evironment variable "DOCKER_HUB_USERNAME"')

if DOCKER_HUB_PASSWORD is None:
    raise AttributeError('Missing evironment variable "DOCKER_HUB_PASSWORD"')

if DOCKER_HUB_REPO is None:
    raise AttributeError('Missing evironment variable "DOCKER_HUB_REPO"')

# Optional application settings
ENABLE_LOG_SERVER = os.getenv("ENABLE_LOG_SERVER", "False").lower() in ("true", "1")
LOG_SERVER_IP = os.getenv("LOG_SERVER_IP", "127.0.0.1")
LOG_SERVER_PORT = os.getenv("LOG_SERVER_PORT", "9020")
LOG_LEVEL = level_translator(os.getenv("LOG_LEVEL", "INFO"))

DISABLE_LOGGERS = [
    "werkzeug",
    "docker.utils.config",
    "docker.auth",
    "urllib3.connectionpool"
]

# Log
setup_logging(
    enable_server_handler=ENABLE_LOG_SERVER,
    server_address=LOG_SERVER_IP,
    server_port=LOG_SERVER_PORT,
    logger_level=LOG_LEVEL
)

log = getLogger(APPLICATION_NAME) # pylint: disable=invalid-name
web_app = Flask(APPLICATION_NAME) # pylint: disable=invalid-name
socket_io = SocketIO(web_app) # pylint: disable=invalid-name

@web_app.route("/")
def index():
    """Main endpoint for the web app"""
    if fleet.empty():
        return "No device registered"
    return render_template("index.html", fleet=fleet.get_fleet_information())

@web_app.route("/fleet", methods=['GET'])
def fleet():
    """Endpoint to retrieve data about fleet"""
    return jsonify(fleet.get_fleet_information())


@web_app.route("/telemetry-post", methods=["POST"])
def telemetry():
    """Telemetry consumer"""
    device_telemetry = shared.DeviceTelemetry(**request.get_json())
    log.debug("Telemetry post recieved: %s", device_telemetry)

    fleet.add_telemetry(
        DeviceInformation(
            telemetry=device_telemetry,
            ip_addr=request.remote_addr
        )
    )
    return Response(status=HTTPStatus.ACCEPTED)

def send_command(device_id: str, cmd: shared.Command) -> None:
    """Send commands to the clients

    Args:
        device_id (str): Device ID
        cmd (Command): Command dictionary
    """
    log.debug("Sending command: %s", cmd)
    response = post(url=f'{fleet.get_device_ip(device_id)}/command', json=cmd)


consumers = []

@socket_io.on('connect')
def connect():
    log.info('Device connected, addr: %s, sid: %s', request.remote_addr, request.sid)
    consumers.append(f'{request.remote_addr}:{request.sid}')
    log.info('Device added to known connections. Connection list: %s', consumers)

@socket_io.on('disconnect')
def disconnect():
    log.info('Device disconnected, addr: %s, sid: %s', request.remote_addr, request.sid)
    consumers.remove(f'{request.remote_addr}:{request.sid}')
    log.info('Device removed to known connections. Connection list: %s', consumers)

@socket_io.event
def event_stream(event):
    socket_io.emit('event_stream', event)

@web_app.route("/container-command", methods=['POST'])
def container_command() -> Response:
    """Command entrypoint for containers from the user web app

    Returns:
        Response: HTTP response
    """
    command_info = request.get_json()

    send_command(command_info['id'], command_info)
    return Response(status=HTTPStatus.ACCEPTED)

@web_app.route("/device-command", methods=['POST'])
def device_command() -> Response:
    """Command entrypoint for devices from the user web app

    Returns:
        Response: HTTP response
    """
    command_info = request.get_json()

    if command_info['command'] == 'remove_device':
        fleet.remove_device(command_info['id'])

    return Response(status=HTTPStatus.ACCEPTED)

fleet = None    # pylint: disable=invalid-name

def main():
    """Main program"""
    disable_loggers(DISABLE_LOGGERS)

    try:
        docker_hub = DockerHub(http_get, DOCKER_HUB_USERNAME, DOCKER_HUB_PASSWORD, DOCKER_HUB_REPO)
    except PermissionError:
        log.error('Could not log into Docker hub')
        sys.exit(1)

    global fleet # pylint: disable=global-statement, invalid-name
    fleet = Fleet(docker_hub, consumers, event_stream)

    socket_io.run(
        web_app,
        host='0.0.0.0',
        port=APP_PORT
    )

if __name__ == '__main__':
    main()
