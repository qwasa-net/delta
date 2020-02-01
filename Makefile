#
SHELL := /bin/bash
TIMESTAMP := $(shell date +"%Y%m%d-%H%M")

#
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))
MENAME ?= $(shell basename "$(MAKEFILE_DIR)")
HOME_PATH := $(MAKEFILE_DIR)
ENV_PATH ?= $(HOME_PATH)/_env
PYTHON ?= $(ENV_PATH)/bin/python

# python sorce code linter
PYLINT ?= $(ENV_PATH)/bin/pylint
PYLINT_FLAGS ?= -sy --rcfile=.pylintrc
PYTHON_LINTER ?= $(PYLINT) $(PYLINT_FLAGS)
PYTHON_LINTER_FILES := $(wildcard */*.py)

.PHONY: help

#
help:
	-@grep -E "^[a-z_0-9]+:" "$(strip $(MAKEFILE_LIST))" | grep '##' | sed 's/:.*##/## —/ig' | column -t -s '##'

# create virtual environment
env:
	pip install virtualenv
	virtualenv -p /usr/bin/python3 $(ENV_PATH)
	source $(ENV_PATH)/bin/activate
	$(ENV_PATH)/bin/pip install --upgrade --requirement requirements.txt

#
test_all: test test_commander test_tcpserver

test:  ## run unittests
	$(PYTHON) -m unittest --verbose --failfast

test_commander:  ## test delta commander
	$(PYTHON) clients/delta_commander.py data/dictionary-test.xml \
	--verbose --allow-shell \
	--say "what time is it?"

test_tcpserver:  TEST_TCPSERVER_HOST?=localhost
test_tcpserver:  TEST_TCPSERVER_PORT?=17777
test_tcpserver:  ## test delta simple tcp server
	$(PYTHON) clients/delta_commander.py data/dictionary-test.xml \
	--verbose \
	--tcpserver "$(TEST_TCPSERVER_HOST)" "$(TEST_TCPSERVER_PORT)" --tcpserver-limit 2 &
	@sleep 1
	@echo "hello there" | nc "$(TEST_TCPSERVER_HOST)" "$(TEST_TCPSERVER_PORT)" >/dev/null
	@echo "2+2" | nc "$(TEST_TCPSERVER_HOST)" "$(TEST_TCPSERVER_PORT)" >/dev/null

#
docker_build_tcpserver:
	docker build \
	--tag delta_simple_tcpserver \
	--label name=delta_simple_tcpserver \
	--file docker/simple_tcpserver.dockerfile \
	.
	docker image ls delta_simple_tcpserver

docker_start_tcpserver:
	docker run \
	--publish 17777:17777 \
	--detach \
	--rm \
	--name delta_simple_tcpserver \
	delta_simple_tcpserver
	docker container ls -a --filter name=delta_simple_tcpserver

docker_stop_tcpserver:
	docker container stop -t 3 delta_simple_tcpserver
	docker container ls -a --filter name=delta_simple_tcpserver

#
pylint: $(patsubst %.py,%.pylint,$(PYTHON_LINTER_FILES))  ## run python linter

%.pylint:
	$(PYTHON_LINTER) $*.py
