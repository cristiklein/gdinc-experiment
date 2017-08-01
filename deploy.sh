#!/bin/bash
set -e

if [ -z "`which docker`" ]; then
    echo "Could not find docker." >&2
    echo "Please use the following script to install it: https://get.docker.com/." >&2
    exit 1
fi

if [ -z "$SSH_AUTH_SOCK" ]; then
    echo "Please make sure you run an SSH agent." >&2
    echo "This allows ansible (contained by Docker) to connect to your machines, " >&2
    echo "without having access to the SSK keys." >&2
    exit 1
fi

BASEDIR=$(dirname $(readlink -f "$0"))

echo "Building ansible docker image ..." >&2
(cd docker; docker build -t gdinc-experiment .)

docker run \
    --rm -ti \
    --volume $BASEDIR:/playbook --workdir /playbook \
    --env LANG=C.UTF-8 \
    --env ANSIBLE_HOST_KEY_CHECKING=False \
    --env ANSIBLE_SSH_PIPELINING=1 \
    --env ANSIBLE_STDOUT_CALLBACK=debug \
    --env SSH_AUTH_SOCK=$SSH_AUTH_SOCK \
    --user $(id --user) \
    --volume /etc/passwd:/etc/passwd:ro \
    --volume /etc/group:/etc/group:ro \
    --volume /tmp:/home/$USER \
    --volume $SSH_AUTH_SOCK:$SSH_AUTH_SOCK \
    gdinc-experiment \
    ansible-playbook site.yml --inventory hosts $*
