#!/bin/bash

set -xe

precreate-core jupyter-notebook /opt/nbsearch/solr/jupyter-notebook/
precreate-core jupyter-cell /opt/nbsearch/solr/jupyter-cell/

exec solr -f