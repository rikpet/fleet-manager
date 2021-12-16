# Fleet manager

### ***THIS REPOSITORY IS IN PREVIEW***

This repository is part of a hoppy project to automate every day life. This project is mostly for me to learn new technics and languages, but in the same time building something useful.

Other repositories in this project are:

- [Decentralized logger](https://github.com/rikpet/distributed_logger)

## Introduction to the repository
**Simple tool to handle a network of docker container spread out over several devices.**

The system consists of a client application, which can be installed at every device. The client application gathers data about the device and docker containers on the device and sends it to the server application. The client can handle easier commands, such as start and stop containers and updating container to a newer image.

The second application is a server application, which act as a centralized server for data gathering and user interaction. The server has a simple web application which enables an user to interact with the different devices and containers in the system. The servers enables an user to send command to the different client and can through the web application, for example, update a container to the latest image available.

## Getting started
These application are mainly built for being deployed with docker containers. 

Docker images are available [here](https://hub.docker.com/repository/docker/rikpet/easy-living/).

The Docker images is often available in two different version:
- ``beta``: latest development version, will most likely include issues
- ``stable``: latest stable and tested version.

### Server
*Docker image name: ``fl-server-[stable/beta]``*

The server application can either ran as a python application or inside a docker container. This tutorial will focus on running the application in a docker container on a raspberry pi.

1. Install docker by running the following command:
    ```bash 
    curl -sSL https://get.docker.com | sh
    ```

2. Create an account on [Docker hub](https://hub.docker.com/). This is needed for the version control to work.

3. There are four environment variables needed for the application to run. These can either be added when starting the container, but if you want to use the composer file these needs to be added before. 

    The enviroment variables needed are:

    - **DOCKER_HUB_USERNAME** - Username for the Docker hub account
    - **DOCKER_HUB_PASSWORD** - Password for the Docker hub account
    - **DOCKER_HUB_REPO** - Docker hub repository where the images can be found. Should be ``rikpet/easy-living`` if the purpose is to use this repository, but this variable can be pointed towards another repo if wanted. Note that the docker hub account need access to the repository for this application to work as intended.

4. Start the container. There are a ``docker-compose.yaml`` to help out creating the container. Download the composer file to the device, change which version to use (stable or beta) in the file and run:
    ```bash
    docker-compose --file docker-compose.yaml up -d
    ```

5. The application should be running now. Open a web browser on any device in the same network and go to:
    ```bash
    [ip to the device]:5010
    ```
    If no device are registered the page will we empty but as soon as a device is registered (through the device application) the UI will appear.

### Client
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

To build the docker image run:

```bash
make build-server
```

To start the container run:

```bash
make run-server
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
