"""Fleet manager client

This client reads the status of docker containers installed on the same device and sends
data about the device and docker container to the fleet management server.

The client is also capable to handle commands from the server and interacts with the
containers.
"""

from logging import getLogger
import threading
from uuid import getnode
import time
import os
import socketio
from socketio.exceptions import BadNamespaceError, ConnectionError as SocketConnectionError
from decentralized_logger import setup_logging, disable_loggers, level_translator

from device import Device

APPLICATION_NAME = "fleet-manager-client"

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
socket_io = socketio.Client() # pylint: disable=invalid-name

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


@socket_io.event
def telemetry(telemetry_post):
    """Socket endpoint to handle telemetry flow to the server

    Args:
        telemetry_post (dict): telemetry post to be sent to server
    """
    log.debug('Sending telemetry: %s', telemetry_post)
    try:
        socket_io.emit('telemetry', telemetry_post)
    except BadNamespaceError:
        log.warning("Could not send telemetry to server at %s", fleet_manager_server_url())

@socket_io.on(f'command_{DEVICE_ID}')
def command(cmd):
    """Command endpoint for the client

    Args:
        cmd (dict): Command for the client
    """
    log.debug('Command received: %s', cmd)
    command_interpreter(cmd)
    fleet_manager.send_telemetry()

def command_interpreter(command_dict):
    """Command interpreter. Read incomming command dict and translate it
    into real actions

    Args:
        command_dict (dict): Command dictionary
    """
    if command_dict['command'] == 'stop_container':
        device.stop_container(command_dict['container_name'])
    elif command_dict['command'] == 'start_container':
        device.start_container(command_dict['container_name'])
    elif command_dict['command'] == 'update_container':
        device.update_container(command_dict['container_name'])
    #TODO: Add handling for if the command doesn't exist

def main():
    """Main function"""
    disable_loggers(DISABLE_LOGGERS)

    device.update()
    fleet_manager.start()

    while True:
        try:
            socket_io.connect(fleet_manager_server_url() +'?ignore-me=True', transports='websocket')
        except SocketConnectionError:
            log.warning('Could not connect to log server')
            time.sleep(PUSH_INTERVAL)
        else:
            log.info('Connected to server')
            socket_io.wait()


if __name__ == '__main__':
    main()
