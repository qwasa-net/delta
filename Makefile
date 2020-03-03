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


env:  ## create virtual environment
	pip3 install virtualenv
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
docker_build_tcpserver:  ## demo tcp client -- build docker image
	docker build \
	--tag delta_simple_tcpserver \
	--label name=delta_simple_tcpserver \
	--file deploy/docker/simple_tcpserver.dockerfile \
	.
	docker image ls delta_simple_tcpserver

docker_start_tcpserver:  ## demo tcp client -- start docker container (localhost:17777)
	docker run \
	--publish 17777:17777 \
	--detach \
	--rm \
	--name delta_simple_tcpserver \
	delta_simple_tcpserver
	docker container ls -a --filter name=delta_simple_tcpserver

docker_stop_tcpserver:   ## demo tcp client -- stop docker container
	docker container stop -t 3 delta_simple_tcpserver
	docker container ls -a --filter name=delta_simple_tcpserver

#
docker_build_tgbot:  ## tgbot -- build docker image
	docker build \
	--tag delta_tgbot \
	--label name=delta_tgbot \
	--file deploy/docker/tgbot.dockerfile \
	.
	docker image ls delta_tgbot

docker_start_tgbot: DELTATG_WEBHOOK_URL?=/
docker_start_tgbot: DELTATG_API_TOKEN?=~TOKEN~
docker_start_tgbot: RESTART_POLICY?=no
docker_start_tgbot: docker_build_tgbot  ## tgbot -- start docker container (local, DELTATG_WEBHOOK_URL=…, DELTATG_API_TOKEN=…)
	docker run \
	--publish 17780:17780 \
	--restart $(RESTART_POLICY) \
	--env DELTATG_WEBHOOK_URL="$(DELTATG_WEBHOOK_URL)" \
	--env DELTATG_API_TOKEN="$(DELTATG_API_TOKEN)" \
	--detach \
	--name delta_tgbot \
	delta_tgbot
	docker container ls -a --filter name=delta_tgbot

docker_stop_tgbot:  ## tgbot -- stop docker container (local)
	-docker container ls -a --filter name=delta_tgbot
	-docker container stop -t 3 delta_tgbot
	-docker container ls -a --filter name=delta_tgbot

docker_push_image_tgbot: REGISTRY?=qwasa.net/delta
docker_push_image_tgbot:  ## tgbot -- push image to registry (REGISTRY=…)
	docker push $(REGISTRY):latest

docker_copy_image_remote_tgbot: DEPLOY_HOST?=localhost
docker_copy_image_remote_tgbot: docker_build_tgbot  ## tgbot -- build image and copy to remote host (DEPLOY_HOST=…)
	docker save delta_tgbot | ssh $(DEPLOY_HOST) docker load

docker_start_remote_tgbot: DEPLOY_HOST?=localhost
docker_start_remote_tgbot: DELTATG_WEBHOOK_URL?=/
docker_start_remote_tgbot: DELTATG_API_TOKEN?=~TOKEN~
docker_start_remote_tgbot: docker_stop_remote_tgbot docker_copy_image_remote_tgbot  ## tgbot -- copy and run image on remote host (DEPLOY_HOST=…)
	ssh $(DEPLOY_HOST) docker run \
	--restart unless-stopped \
	--publish 17780:17780 \
	--env DELTATG_WEBHOOK_URL="$(DELTATG_WEBHOOK_URL)" \
	--env DELTATG_API_TOKEN="$(DELTATG_API_TOKEN)" \
	--detach \
	--name delta_tgbot \
	delta_tgbot
	ssh $(DEPLOY_HOST) docker container ls -a --filter name=delta_tgbot

docker_stop_remote_tgbot: DEPLOY_HOST?=localhost
docker_stop_remote_tgbot:  ## tgbot -- stop docker container (DEPLOY_HOST=…)
	-ssh $(DEPLOY_HOST) 'docker container stop -t 1 delta_tgbot; docker container rm delta_tgbot'

copy_files_remote: DEPLOY_HOST?=localhost
copy_files_remote: ## copy all files to remote host (DEPLOY_HOST=…)
	-@git archive --format tar.gz --prefix delta/ master | ssh $(DEPLOY_HOST) 'gunzip -c | tar xv'

pylint: $(patsubst %.py,%.pylint,$(PYTHON_LINTER_FILES))  ## run python linter

%.pylint:
	$(PYTHON_LINTER) $*.py
