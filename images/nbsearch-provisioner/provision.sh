#!/bin/bash

set -xe

if [[ ! -f /user-notebooks/.nbsearchignore ]] ; then
    cp -f /.nbsearchignore /user-notebooks/
fi
