#!/bin/bash

docker-compose -f docker-compose.yml -f docker-compose.nbsearch.yml run --rm nbsearch-crawler \
    jupyter nbsearch update-index --debug /opt/conda/etc/jupyter/jupyter_notebook_config.py local