############################
# Dockerfile to build audiobook server
# Based on Ubuntu
############################

# Set the base image to Ubuntu
FROM ubuntu:16.04

# File Author / Maintainer
MAINTAINER Example Huy

# Update the repository sources list
RUN apt-get update

RUN apt-get -y install vim-tiny python python-twisted curl unzip && \
    curl -Lk https://github.com/hdo/audiobookserver/archive/master.zip -o /tmp/master.zip && \
    unzip /tmp/master.zip -d / && \
    rm /tmp/master.zip
# Expose the default port
EXPOSE 9090

ENTRYPOINT python /audiobookserver-master/staticserver.py
