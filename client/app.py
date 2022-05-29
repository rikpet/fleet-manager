"""Fleet manager client

This client reads the status of docker containers installed on the same device and sends
data about the device and docker container to the fleet management server.

The client is also capable to handle commands from the server and interacts with the
containers.
"""

from cgitb import text
from logging import getLogger
import threading
from uuid import getnode
from http import HTTPStatus
import time
import os
from shutil import copyfile
from flask import Flask, request, Response
import requests
from decentralized_logger import setup_logging, disable_loggers, level_translator

from device import Device
from shared.commands import Command, CommandType

APPLICATION_NAME = "fleet-manager-client"

DEVICE_COMPOSE_FILE = os.path.join("share", "device_compose.yaml")
BASE_COMPOSE_FILE = "base_compose.yaml"

# Environment variables
PUSH_INTERVAL = int(os.getenv("PUSH_INTERVAL", "60"))
DEVICE_NAME = os.getenv("DEVICE_NAME", "John Doe")
FM_SERVER_ADDRESS = os.getenv("FLEET_MANAGER_SERVER_ADDRESS", "127.0.0.1")
FM_SERVER_PORT = os.getenv("FLEET_MANAGER_SERVER_PORT", "5010")

ENABLE_LOG_SERVER = os.getenv("ENABLE_LOG_SERVER", "False").lower() in ("true", "1")
LOG_SERVER_IP = os.getenv("LOG_SERVER_IP", "127.0.0.1")
LOG_SERVER_PORT = os.getenv("LOG_SERVER_PORT", "9020")
LOG_LEVEL = level_translator(os.getenv("LOG_LEVEL", "INFO"))

DEVICE_ID = hex(getnode())[2:]

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

class FleetManagerClient(threading.Thread):
    """Handles telemetry events and sends telemetry to the server based on the push interval.

    New thread is started to handle the push events

    Args:
        push_interval (int): Push interval for the telemetry
    """

    SERVER_ENDPOINT = "entry"

    def __init__(self, push_interval) -> None:
        threading.Thread.__init__(self)

        self.push_interval = push_interval
        self.event = threading.Event()
        self.log = getLogger(self.__class__.__name__)

    def run(self):
        self.log.info("Starting fleet manager client")
        while True:
            start = time.time()

            device.update()
            device_summary_object = device.information()
            device_summary_object["push_interval"] =  self.push_interval

            self.log.debug("New device object created: %s", device_summary_object)
            telemetry(device_summary_object)

            self.event.clear()
            self.event.wait(timeout=max(self.push_interval - (time.time() - start), 0))

    def send_telemetry(self):
        """
        Send telemetry, bypasses the telemetry push
        interval and sends a new telemetry post to server
        """
        self.event.set()

def fleet_manager_server_url():
    """Parsing server URL"""
    return f'http://{FM_SERVER_ADDRESS}:{FM_SERVER_PORT}'


fleet_manager = FleetManagerClient(PUSH_INTERVAL)
device = Device(fleet_manager_server_url(), DEVICE_NAME, DEVICE_ID)


def telemetry(telemetry_post):
    """Socket endpoint to handle telemetry flow to the server

    Args:
        telemetry_post (dict): telemetry post to be sent to server
    """
    log.debug('Sending telemetry: %s', telemetry_post)
    response = requests.post(url=fleet_manager_server_url(), json=telemetry_post)
    if response.status_code is not HTTPStatus.ACCEPTED:
        log.warning("Could not send telemetry to server at %s. Response code: %s Response message: %s", fleet_manager_server_url(), response.status_code, response.text)

# TODO: change to case/switch when updating to python 3.10
@app.route("/command")
def command():
    """Command endpoint for the client

    Args:
        cmd (dict): Command for the client
    """
    cmd = Command(**request.get_json())
    log.debug('Command received: %s', cmd)

    if cmd.type == CommandType.StopContainer:
        device.stop_container(cmd['container_name'])

    elif cmd.type == CommandType.StartContainer:
        device.start_container(cmd['container_name'])

    elif cmd.type == CommandType.UpdateDevice:
        device.update_container(cmd['container_name'])

    elif cmd.type == CommandType.ReadCompose:
        with open(DEVICE_COMPOSE_FILE, "r") as f:
            return Response(status=HTTPStatus.OK, text=f.read())

    elif cmd.type == CommandType.WriteCompose:
        with open(DEVICE_COMPOSE_FILE, "w") as f:
            f.write(cmd.payload['content'])
        return Response(status=HTTPStatus.ACCEPTED)

    fleet_manager.send_telemetry()

def check_environment():
    if not os.path.exists(DEVICE_COMPOSE_FILE):
        copyfile(BASE_COMPOSE_FILE, DEVICE_COMPOSE_FILE)

def update_device():
    pass

def main():
    """Main function"""
    disable_loggers(DISABLE_LOGGERS)

    check_environment()

    device.update()
    fleet_manager.start()

    app.run(
        host='0.0.0.0',
        port=5000
    )

if __name__ == '__main__':
    main()
