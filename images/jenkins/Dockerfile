FROM jenkins/jenkins:lts

# Jenkins is running as root to manipulate docker
USER root

RUN curl -fsSL https://get.docker.com | sh
RUN apt-get update && \
    apt-get install -y zip && \
    apt-get autoclean && apt-get clean && apt-get autoremove

RUN jenkins-plugin-cli --plugins \
        "oic-auth" "build-timeout" "discard-old-build" slack
