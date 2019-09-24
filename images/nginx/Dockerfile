FROM nginx:stable

RUN ln -sfT /dev/stderr "/var/log/nginx/error.log" && \
    ln -sfT /dev/stdout "/var/log/nginx/access.log"

RUN rm -f /etc/localtime
