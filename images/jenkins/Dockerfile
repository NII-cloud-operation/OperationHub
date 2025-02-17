FROM jenkins/jenkins:lts

USER root

RUN curl -fsSL https://get.docker.com | sh

USER jenkins
RUN jenkins-plugin-cli --plugins "oic-auth"
