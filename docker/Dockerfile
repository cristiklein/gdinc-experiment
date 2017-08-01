FROM ubuntu:16.04
MAINTAINER Cristian Klein <cristiklein@gmail.com>

RUN \
    apt-get update \
    && apt-get install -y software-properties-common

RUN \
    apt-add-repository ppa:ansible/ansible \
    && apt-get update \
    && apt-get install -y ansible

RUN \
    apt-get update \
    && apt-get install -y rsync

VOLUME /playbook
