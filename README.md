# OperationHub

A simple JupyterHub for *Literate Computing for Reproducible Infrastructure*.

OperationHub helps you provide a multi-user notebook environment on a single server
for a small operation team to start *Literate Computing for Reproducible Infrastructure*.

It serves the following features:

- A multi-user notebook environment by JupyterHub on a single server
- Each user environment is isolated by a docker container
- Password authentication by PAM
- Sharing notebooks between users
   - Read-only shared directory for users to view each other's notebooks
   - Writable shared directory by any users

# Installation

## Prerequisites

- A CentOS 7 server you have root access
- Python 3.6 or later
- Docker Engine and Docker Compose
- TLS certificate and private key for HTTPS communication
- Domain name and IP address

## Step 1: Download OperationHub files

Clone this repository to the server, change current working directory to the repository directory.

    $ git clone https://github.com/NII-cloud-operation/OperationHub.git
    $ cd OperationHub

## Step 2: Install Docker Engine and docker-compose

Docker Engine and Docker Compose are required.
You can install with `install-docker.sh` script.

    $ sudo ./install-docker.sh

## Step 3: Install the host services for OperationHub

OperationHub is running inside a docker container,
however, requires some services are running on a host system.
Please install the services with `install-host-services.sh` script.

    $ sudo ./install-host-services.sh

This script installs python 3 environment and the following systemd units.

- `restuser.service`
  - RESTUser service ( https://github.com/minrk/restuser )
  - REST API server for creating users on the host system
- `ophubuser.service`
  - REST API server for operation on the host system
  - It provides an API to mount user's notebook directory to a shared directory
- `copy-passwd.path`
- `copy-passwd.service`
  - If  `/etc/passwd`,  `/etc/shadow` and `/etc/group` are modifed, the units copy these files to `/var/lib/jupyterhub/passwd` to sync host and container users

## Step 4: Setting domain name

Create the environment file named `.env` to the same directory of `docker-copmose.yml`.
Write the following contents to `.env` file with a text editor like vi.

    SERVER_NAME=(your domain name)

This domain name is used for the TLS domain name.

## Step 5: Install TLS certificate and key

Put TLS certificate and key files to the following path.

- ./cert/server.cer: The server certificate file
- ./cert/server.key: The private key file (no passphrase)

If intermediate certificate file is requires, concatenate intermediate certificate and server certificate file.

## Step 6: Setting JupyterHub administrator

Before you start OperationHub, make an administrator user.
If the Linux user is a member of `wheel` group, the user has administrator privileges of the JupyterHub.
If you want to make a user an administrator, execute the following command.

    $ sudo usermod -aG wheel (username)

## Step 7: Starting OperationHub

Start OperationHub with `docker-compose`

    $ sudo docker-compose build
    $ sudo docker-compose up -d

Try accessing https://(your domain name)/ from your browser.
If everything went well, you should see a JupyterHub login page.

**Caution:** The default image is better to be loaded beforehand to avoid a long wait and a possible time-out. 

# Create new user

For creating a new user, use `useradd` command on the command line of the server.

    $ sudo useradd (username)

Alternatively, add a user with the 'Add Users' button in the JupyterHub admin interface.

The new user cannot log in before setting a password by `passwd` command.

# The image to use for single-user servers

The default image is [niicloudopration/notebook](https://hub.docker.com/r/niicloudoperation/notebook/).
You can build a custom image of a single-user server from this image.

If the image does not exist on a local server when starting a single-user server, JupyterHub will pull it automatically.
However, if the image is large, starting a server may fail with a timeout.
You can pull it in advance.

# Options

You can customize the OperationHub settings by `.env` file.

About `.env` file details, see [Environment variables in Compose](https://docs.docker.com/compose/environment-variables/#the-env-file)

The following is a list of environment variables that can be set.

**SERVER_NAME**

`SERVER_NAME` is the web server name for TLS.

Example:

    SERVER_NAME=ophub.example.com

**SERVER_PORT**

The web server port. The default is 443.

**SINGLE_USER_IMAGE**

`SINGLE_USER_IAMGE` is the name of the docker image to use for a single-user notebook server.

Example:

    SINGLE_USER_IMAGE=niicloudoperation/notebook

**CULL_ENABLE**

If CULL_ENABLE is `yes` or `1`, enables culling idle single-user servers. The default value is `no`.

**CULL_SERVER_IDLE_TIMEOUT**

The idle timeout (in seconds) for culling idle servers.

**CULL_SERVER_MAX_AGE**

The maximum age (in seconds) of servers that should be culled even if they are active.

**CULL_SERVER_EVERY**

The interval (in seconds) for checking for idle servers to cull.

**LC_WRAPPER_FLUENTD_HOST**, **LC_WRAPPER_FLUENTD_PORT**

The [Jupyter-LC_wrapper](https://github.com/NII-cloud-operation/Jupyter-LC_wrapper) can send 
cell execution results to a Fluentd forward server.
For using this feature, set the address and port of the Fluentd forward server to `LC_WRAPPER_FLUENTD_HOST`, `LC_WRAPPER_FLUENTD_PORT`.

**SIDESTICKIES_SCRAPBOX_PROJECT_ID**, **SIDESTICKIES_SCRAPBOX_COOKIE_CONNECT_SID**

The [Scrapbox](https://scrapbox.io/) project name and access token for [sidestickies](https://github.com/NII-cloud-operation/sidestickies) extension.

The [niicloudopration/notebook](https://hub.docker.com/r/niicloudoperation/notebook/) image includes sidestickies extension.
You can enable sidestickies extension via the Nbextensions tab. Note: you need to enable both "Sidestickies for file tree" and "Sidestickies for notebook" nbextensions.

**NBSEARCHDB_HOSTNAME**, **NBSEARCHDB_PORT**,  
**NBSEARCHDB_USERNAME**, **NBSEARCHDB_PASSWORD**,  
**NBSEARCHDB_DATABASE**, **NBSEARCHDB_COLLECTION**,  
**NBSEARCHDB_MY_SERVER_URL**,  
**NBSEARCHDB_AUTO_UPDATE**

The configurations for [NBSearch](https://github.com/NII-cloud-operation/nbsearch).

See https://github.com/NII-cloud-operation/Jupyter-LC_docker#using-nbsearch about details.

# Collecting container logs

OperationHub outputs logs such as Nginx access logs and JupyterHub logs to docker logs.
If you want to collect these container logs of OperationHub, configure logging drivers of Docker.

Example of docker `daemon.json` when collecting logs with fluentd:

    {
        "log-driver": "fluentd",
        "log-opts": {
            "fluentd-address": "127.0.0.1:24224",
            "fluentd-async-connect": "true",
            "tag": "logs.docker.container.{{.Name}}.{{.ID}}"
         }
     }


About logging drivers configuration, please see "[Configure logging drivers](https://docs.docker.com/config/containers/logging/configure/)"

# Directory layout

## In a container filesystem of a single-user server

**/home/USERNAME/**

User's home directory. Users can put their credential files to a directory under this directory, for example, `/home/USERNAME/.ssh`.

**/home/USERNAME/notebooks/**

Each user's notebook root directory for the notebook server.
The files under this directory are shared with other users.

**/home/USERNAME/notebooks/users/**

All users can read other user's notebook directories through this directory.
It is a read-only filesystem.

**/home/USERNAME/notebooks/share/**

The shared notebook directory. All users can read/write to this directory.

## In a host filesystem

**/home/USERNAME/**

User's home directory, mounted from /home/USERNAME in a container.

**/home/user-notebooks/**

Read-only shared notebook directory, mounted from `/home/USERNAME/notebooks/users/` in a container.

**/var/lib/jupyterhub/share/**

Writable shared notebook directory, mounted from `/home/USERNAME/notebooks/share/` in a container.
Its permission and ACL is set to writable by any users when JupyterHub start.

**/var/lib/jupyterhub/data/**

This directory contains data files related to JupyterHub, for example, the SQLite DB file.

**/var/lib/jupyterhub/passwd/**

This directory is used to sync host and container users.

## About Internals

![internals](docs/internals.png)
