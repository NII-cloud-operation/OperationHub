#!/bin/bash

set -xe

if [[ ! -f /user-notebooks/.nbsearchignore ]] ; then
    cp -f /solr/.nbsearchignore /user-notebooks/
fi