FROM solr:8

USER root

COPY ./nbsearch /opt/nbsearch
COPY ./start.sh /start.sh
RUN chmod 0755 /start.sh

USER solr

ENTRYPOINT /start.sh
