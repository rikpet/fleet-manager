"""Fleet manager client

This client reads the status of docker containers installed on the same device and sends
data about the device and docker container to the fleet management server.

The client is also capable to handle commands from the server and interacts with the
containers.
"""

from logging import getLogger
import threading
from uuid import getnode
from http import HTTPStatus
import time
import os
import shutil
from flask import Flask, request, Response
import requests
from requests.exceptions import ConnectionError as HttpConnectionError
from decentralized_logger import setup_logging, disable_loggers, level_translator


# Feature flags
DEVELOPMENT_MODE = os.getenv("ENV", "").lower() == "development"

if DEVELOPMENT_MODE:
    import sys

    parent_path = os.path.dirname(os.getcwd())
    sys.path.append(parent_path)

from device import Device   # pylint: disable=wrong-import-position
import shared               # pylint: disable=wrong-import-position


# Constants
APPLICATION_NAME = "fleet-manager-client"
APP_PORT = 5000
DEVICE_COMPOSE_FILE = os.path.join("share", "device_compose.yaml")
BASE_COMPOSE_FILE = "base_compose.yaml"
DEVICE_ID = hex(getnode())[2:]

if DEVELOPMENT_MODE:
    DEVICE_COMPOSE_FILE = "docker-compose.yaml"
    APP_PORT = 5011

# Application settings
PUSH_INTERVAL = int(os.getenv("PUSH_INTERVAL", "60"))
DEVICE_NAME = os.getenv("DEVICE_NAME", "John Doe")
FM_SERVER_ADDRESS = os.getenv("FLEET_MANAGER_SERVER_ADDRESS", "127.0.0.1")
FM_SERVER_PORT = os.getenv("FLEET_MANAGER_SERVER_PORT", "5010")

ENABLE_LOG_SERVER = os.getenv("ENABLE_LOG_SERVER", "False").lower() in ("true", "1")
LOG_SERVER_IP = os.getenv("LOG_SERVER_IP", "127.0.0.1")
LOG_SERVER_PORT = os.getenv("LOG_SERVER_PORT", "9020")
LOG_LEVEL = level_translator(os.getenv("LOG_LEVEL", "INFO"))


DISABLE_LOGGERS = [
    "werkzeug",
    "docker.utils.config",
    "docker.auth",
    "urllib3"
]

# Log
setup_logging(
    enable_server_handler=ENABLE_LOG_SERVER,
    server_address=LOG_SERVER_IP,
    server_port=LOG_SERVER_PORT,
    logger_level=LOG_LEVEL
)

log = getLogger(APPLICATION_NAME) # pylint: disable=invalid-name
app = Flask(APPLICATION_NAME)

if DEVELOPMENT_MODE:
    log.warning("Development mode activated")


def fleet_manager_server_url():
    """Parsing server URL"""
    return f'http://{FM_SERVER_ADDRESS}:{FM_SERVER_PORT}'


def check_environment():
    """Checking for composer file describing environment"""
    if not os.path.exists(DEVICE_COMPOSE_FILE):
        shutil.copyfile(BASE_COMPOSE_FILE, DEVICE_COMPOSE_FILE)


class FleetManagerClient(threading.Thread):
    """Handles telemetry events and sends telemetry to the server based on the push interval.

    New thread is started to handle the push events
    """

    def __init__(self) -> None:
        threading.Thread.__init__(self)

        self.event = threading.Event()
        self.log = getLogger(self.__class__.__name__)

    def run(self):
        self.log.info("Starting fleet manager client")
        while True:
            start = time.time()

            device_summary_object = device.information()

            self.log.debug("New device object created: %s", device_summary_object)
            send_telemetry(device_summary_object)

            self.event.clear()
            self.event.wait(timeout=max(PUSH_INTERVAL - (time.time() - start), 0))

    def send_telemetry(self):
        """
        Send telemetry, bypasses the telemetry push
        interval and sends a new telemetry post to server
        """
        self.event.set()


fleet_manager = FleetManagerClient()
device = Device(DEVICE_NAME, DEVICE_ID)


def send_telemetry(telemetry: shared.DeviceTelemetry):
    """Socket endpoint to handle telemetry flow to the server

    Args:
        telemetry_post (dict): telemetry post to be sent to server
    """
    log.debug('Sending telemetry: %s', telemetry)
    try:
        response = requests.post(
            url=f'{fleet_manager_server_url()}/telemetry-post',
            json=telemetry.to_json()
        )

        if response.status_code != HTTPStatus.ACCEPTED:
            log.warning(
                "Could not send telemetry to server at %s. Response code: %s Response message: %s",
                fleet_manager_server_url(),
                response.status_code,
                response.text
            )
    except HttpConnectionError:
        log.warning('Could not connect to server')


# TODO: change to case/switch when updating to python 3.10
@app.route("/command")
def command():
    """Command endpoint for the client

    Args:
        cmd (dict): Command for the client
    """
    cmd = shared.Command(**request.get_json())
    log.debug('Command received: %s', cmd)

    if cmd.type == shared.CommandType.STOP_CONTAINER:
        device.stop_container(cmd['container_name'])

    elif cmd.type == shared.CommandType.START_CONTAINER:
        device.start_container(cmd['container_name'])

    elif cmd.type == shared.CommandType.UPDATE_DEVICE:
        pass
        #evice.update_container(cmd['container_name'])

    elif cmd.type == shared.CommandType.READ_COMPOSER:
        with open(DEVICE_COMPOSE_FILE, "r", encoding="utf-8") as f:
            return Response(status=HTTPStatus.OK, response=f.read())

    elif cmd.type == shared.CommandType.WRITE_COMPOSER:
        with open(DEVICE_COMPOSE_FILE, "w", encoding="utf-8") as f:
            f.write(cmd.payload['content'])
        return Response(status=HTTPStatus.ACCEPTED)

    fleet_manager.send_telemetry()


def update_device():
    pass


def main():
    """Main function"""
    disable_loggers(DISABLE_LOGGERS)
    check_environment()
    fleet_manager.start()

    app.run(
        host='0.0.0.0',
        port=APP_PORT
    )

if __name__ == '__main__':
    main()
