# Fleet manager
Tool to handle a network of docker container spread out over several devices. 

The system consists of a client application, which can be installed at every device. The client application gathers data about the device and docker containers on the device and sends it to the server application. The client can handle easier commands, such as start and stop containers and updating container to a newer image.

The second application is a server application, which act as a centralized server for data gathering and user interaction. The server has a simple web application which enables an user to interact with the different devices and containers in the system. The servers enables an user to send command to the different client and can through the web application, for example, update a container to the latest image available

## Install
Both application are compatible with docker containers. 

### Server
To build the docker image run:

```bash
make build-server
```

To start the container run:

```bash
make run-server
```

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

### Windows
A ``Makefile`` is available to help with development, to utilize this tool on windows, install GnuWin32 by in command line type:

```bash
winget install GnuWin32.Make
```

Also be sure to add the path to GnuWin32 in your ``PATH``.
GnuWin32 can usually be found at 

```bash
C:\Program Files (x86)\GnuWin32\bin
```
