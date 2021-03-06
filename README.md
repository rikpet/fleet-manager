# Fleet manager

### ***THIS REPOSITORY IS IN PREVIEW***

This repository is part of a hobby project to automate every day life. This project is mostly for me to learn new technics and languages, but in the same time building something useful.

Other repositories in this project are:

- [Decentralized logger](https://github.com/rikpet/decentralized-logger)

## Introduction to the repository
**Simple tool to handle a network of docker container spread out over several devices.**

The system consists of a client application, which can be installed at every device. The client application gathers data about the device and docker containers on the device and sends it to the server application. The client can handle easier commands, such as start and stop containers and updating container to a newer image.

The second application is a server application, which act as a centralized server for data gathering and user interaction. The server has a simple web application which enables an user to interact with the different devices and containers in the system. The servers enables an user to send command to the different client and can through the web application, for example, update a container to the latest image available.

> **NOTE:** The server application can only gather information about images were the Docker hub account have access to.

## Getting started
These application are mainly built for being deployed with docker containers. 

Docker images are available [here](https://hub.docker.com/repository/docker/rikpet/easy-living/).

The Docker images is often available in two different version:
- ``beta``: latest development version, will most likely include issues
- ``stable``: latest stable and tested version.

### Server
*Docker image name: ``fm-server-[stable/beta]``*

The server application can either ran as a python application or inside a docker container. This tutorial will focus on running the application in a docker container on a raspberry pi.

1. Make sure the system is up to date:
    ```bash
    sudo apt-get update
    sudo apt-get upgrade
    ```

2. Install docker on the device:
    ```bash
    curl -sSL https://get.docker.com | bash
    ```

3. To remove the need of using ``sudo`` prefix when running docker commands, your current user can be added to the Docker group by running:
    ```bash
    sudo usermod -aG docker ${USER}
    ```

    Check that your user is a part of the group by running:
    ```bash
    groups ${USER}
    ```

4. To install Docker compose we first need to determine which version to use and architecture of the hardware. It is recommended to use the latest version of docker compose. Docker compose versions can be found [here](https://github.com/docker/compose/releases). For architecture, if this is installed on a raspberry pi 3 or 4, use ``armv7``, for raspberry pi zero, use ``armv6``.

    ```bash
    sudo curl -L "https://github.com/docker/compose/releases/download/v[VERSION]/docker-compose-linux-[ARCHITECTURE]" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```

5. Create an account on [Docker hub](https://hub.docker.com/). This is needed for the version control to work.

6. Set environment variables (for raspberry pi, this can be done in ``/etc/environment`` in the form of ``VARIABLE=value``). Note that required environment variables must be set for the application to start

    | Variable | Importance | Description |
    |----------|------------|-------------|
    | DOCKER_HUB_USERNAME | Required | Username for the Docker hub account |
    | DOCKER_HUB_PASSWORD | Required | Password for the Docker hub account |
    | DOCKER_HUB_REPO | Required | Docker hub repository where the images can be found. Should be ``rikpet/easy-living`` if the purpose is to use this repository, but this variable can be pointed towards another repo if wanted. Note that the docker hub account need access to the repository for this application to work as intended |
    | ENABLE_LOG_SERVER | Optional | Enable ``decentralized logger``, defaults to ``False`` |
    | LOG_SERVER_IP | Optional | IP to ``decentralized logger``, defaults to ``127.0.0.1``
    | LOG_SERVER_PORT | Optional | Port for ``decentralized logger``, defaults to ``9020`` |
    | LOG_LEVEL | Optional | Logger level, defaults to ``INFO`` |

7. Start the container. There is a template ``docker-compose.yaml`` in the repository to help create the container. To download the template file run:
    ```
    curl -sSL https://raw.githubusercontent.com/rikpet/fleet-manager/main/server/docker-compose.yaml -o [FILE_NAME].yaml
    ```

    Change the composer file accordingly, for example which version to use (stable or beta) in the file and then run:
    ```bash
    docker-compose --file docker-compose.yaml up -d --remove-orphans
    ```

8. The application should now be running. Open a web browser on any device in the same network and go to:
    ```bash
    [ip_to_the_device]:5010
    ```
    If no device is registered the page will be empty, but as soon as a device is registered (through the device application) the UI will appear.

### Client
*Docker image name: ``fm-client-[stable/beta]``*

The client application can either ran as a python application or inside a docker container. This tutorial will focus on running the application in a docker container on a raspberry pi.

1. Follow steps 1 - 4 from the Server getting started guide above to install Docker and Docker compose.

2. Set environment variables (for raspberry pi, this can be done in ``/etc/environment`` in the form of ``VARIABLE=value``).

    | Variable | Importance | Description |
    |----------|------------|-------------|
    | PUSH_INTERVAL | Optional | Push interval for telemetry in seconds, defaults to ``60`` |
    | DEVICE_NAME | Optional | Hardware device name displayed in server UI, defaults to ``John Doe`` |
    | FLEET_MANAGER_SERVER_ADDRESS | Optional | IP address to device running fleet manager server applciation, defaults to ``127.0.0.1`` |
    | FLEET_MANAGER_SERVER_PORT | Optional | Port used by the fleet manager server application, defaults tp ``5010`` |
    | ENABLE_LOG_SERVER | Optional | Enable ``decentralized logger``, defaults to ``False`` |
    | LOG_SERVER_IP | Optional | IP to ``decentralized logger``, defaults to ``127.0.0.1``
    | LOG_SERVER_PORT | Optional | Port for ``decentralized logger``, defaults to ``9020`` |
    | LOG_LEVEL | Optional | Logger level, defaults to ``INFO`` |

3. Start the container. There is a template ``docker-compose.yaml`` in the repository to help create the container. To download the template file run:
    ```
    curl -sSL https://raw.githubusercontent.com/rikpet/fleet-manager/main/client/docker-compose.yaml -o [FILE_NAME].yaml
    ```

    Change the composer file accordingly, for example which version to use (stable or beta) in the file and then run:
    ```bash
    docker-compose --file docker-compose.yaml up -d --remove-orphans
    ```

4. The application should now be running. 


To build the docker image run:

```bash
make build-client
```

To start the container run:

```bash
make run-client
```

## Development
Code follows ``pylint``. Docstrings follow ``Google Python style`` guide docstring format. 

To develop and test this library, install the python dev requirements:

```bash
pip install -r dev_requirements.txt
```

To build the docker image locally run:

```bash
make build-[server/client]
```

To start the container locally run:

```bash
make run-[server/client]
```

The ``Makefile`` has more targets, to get more information and the entire list, run:

```bash
make help
```

### Windows
A ``Makefile`` is available to help with development, to utilize this tool on windows, install GnuWin32 by running the
following command:

```bash
winget install GnuWin32.Make
```

Also be sure to add the path to GnuWin32 in your ``PATH``.
GnuWin32 can usually be found at 

```bash
C:\Program Files (x86)\GnuWin32\bin
```
