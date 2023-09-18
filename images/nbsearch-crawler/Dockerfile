FROM niicloudoperation/notebook

USER root
COPY ./jupyter_notebook_config.py /tmp/crawler_jupyter_notebook_config.py
RUN cat /tmp/crawler_jupyter_notebook_config.py >> $CONDA_DIR/etc/jupyter/jupyter_notebook_config.py

USER $NB_USER
