FROM jupyterhub/jupyterhub:2.3 As builder

# dev tools
RUN apt-get update && \
    apt-get install -y \
        gcc \
        libpq-dev \
        git \
        python3-dev && \
    apt-get autoclean && apt-get clean && apt-get autoremove

# freeze version of pip packages from upstream image
RUN python3 -m pip list --format freeze > /tmp/requirements

WORKDIR /tmp

# nblineage
RUN python3 -m pip wheel --wheel-dir wheelhouse --constraint requirements \
    git+https://github.com/NII-cloud-operation/Jupyter-LC_nblineage.git

# Spawner
RUN python3 -m pip wheel --wheel-dir wheelhouse --constraint requirements \
    git+https://github.com/jupyterhub/dockerspawner.git \
    requests-unixsocket

# Authenticator
COPY authenticator /tmp/authenticator
RUN python3 -m pip wheel --wheel-dir wheelhouse --constraint requirements \
    /tmp/authenticator && \
    rm -rf /tmp/authenticator

FROM jupyterhub/jupyterhub:2.3

# acl
RUN apt-get update && apt-get install -y acl && apt-get autoclean && apt-get clean && apt-get autoremove

RUN python3 -m pip install --no-cache --upgrade setuptools pip

# install the wheels from first stage
COPY --from=builder /tmp/wheelhouse /tmp/wheelhouse
RUN python3 -m pip install --no-cache /tmp/wheelhouse/*

ADD cull_idle_servers.py /usr/local/bin/cull_idle_servers.py
ADD add_user.py /usr/local/bin/add_user.py

RUN mkdir /var/jupyterhub/
ADD jupyterhub_config.py /srv/jupyterhub/
