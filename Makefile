#
SHELL := /bin/bash
TIMESTAMP := $(shell date +"%Y%m%d-%H%M")

#
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))
MENAME ?= $(shell basename "$(MAKEFILE_DIR)")
HOME_PATH := $(MAKEFILE_DIR)
VENV_PATH ?= $(HOME_PATH)/_venv
PYTHON ?= PYTHONPATH=$(HOME_PATH) $(VENV_PATH)/bin/python

# python sorce code linter
RUFF ?= $(VENV_PATH)/bin/python3 -m ruff
PYTHON_LINTER ?= $(RUFF)

SRCFILES := delta clients tests

DOCKER ?= DOCKER_BUILDKIT=1 BUILDKIT_PROGRESS=plain docker

.PHONY: help

#
help:
	-@grep -E "^[a-z_0-9]+:" "$(strip $(MAKEFILE_LIST))" | grep '##' | sed 's/:.*##/## —/ig' | column -t -s '##'

	@echo ===
	@echo make venv format lint test_all
	@echo make docker_build_tgbot docker_copy_image_remote_tgbot DEPLOY_HOST=delta
	@echo make copy_files_remote DEPLOY_HOST=delta
	@echo make docker_start_remote_tgbot DEPLOY_HOST=delta DELTATG_API_TOKEN=000000000:AAbb DELTATG_WEBHOOK_URL=/0123456789abcdef
	@echo make podman_systemd_remote_tgbot DEPLOY_HOST=root@delta
	@echo ===


venv:  ## create virtual environment
	python3 -m venv $(VENV_PATH)
	$(VENV_PATH)/bin/pip install --upgrade --requirement requirements.txt
	$(VENV_PATH)/bin/pip install --upgrade --requirement requirements-dev.txt

# TESTS
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


# DOCKER BUILDS
docker_build_tcpserver:  ## demo tcp client -- build docker image
	$(DOCKER) build \
	--tag delta_simple_tcpserver \
	--label name=delta_simple_tcpserver \
	--file deploy/docker/simple_tcpserver.dockerfile \
	.
	$(DOCKER) image ls delta_simple_tcpserver

docker_start_tcpserver:  ## demo tcp client -- start docker container (localhost:17777)
	$(DOCKER) run \
	--publish 17777:17777 \
	--detach \
	--rm \
	--name delta_simple_tcpserver \
	delta_simple_tcpserver
	$(DOCKER) container ls -a --filter name=delta_simple_tcpserver

docker_stop_tcpserver:   ## demo tcp client -- stop docker container (local)
	$(DOCKER) container stop -t 3 delta_simple_tcpserver
	$(DOCKER) container ls -a --filter name=delta_simple_tcpserver

#
docker_build_tgbot:  ## tgbot -- build docker image
	$(DOCKER) build \
	--tag delta_tgbot \
	--label name=delta_tgbot \
	--file deploy/docker/tgbot.dockerfile \
	.
	$(DOCKER) image ls delta_tgbot

docker_start_tgbot: DELTATG_WEBHOOK_URL?=/
docker_start_tgbot: DELTATG_API_TOKEN?=~TOKEN~
docker_start_tgbot: RESTART_POLICY?=no
docker_start_tgbot: docker_build_tgbot  ## tgbot -- start docker container (local, DELTATG_WEBHOOK_URL=…, DELTATG_API_TOKEN=…)
	$(DOCKER) run \
	--publish 17780:17780 \
	--restart $(RESTART_POLICY) \
	--env DELTATG_WEBHOOK_URL="$(DELTATG_WEBHOOK_URL)" \
	--env DELTATG_API_TOKEN="$(DELTATG_API_TOKEN)" \
	--detach \
	--name delta_tgbot \
	delta_tgbot
	$(DOCKER) container ls -a --filter name=delta_tgbot

docker_stop_tgbot:  ## tgbot -- stop docker container (local)
	-$(DOCKER) container ls -a --filter name=delta_tgbot
	-$(DOCKER) container stop -t 3 delta_tgbot
	-$(DOCKER) container ls -a --filter name=delta_tgbot

docker_push_image_tgbot: REGISTRY?=qwasa.net/delta
docker_push_image_tgbot:  ## tgbot -- push image to registry (REGISTRY=…)
	$(DOCKER) push $(REGISTRY):latest

docker_copy_image_remote_tgbot: DEPLOY_HOST?=localhost
docker_copy_image_remote_tgbot: docker_build_tgbot  ## tgbot -- build image and copy to remote host (DEPLOY_HOST=…)
	$(DOCKER) save delta_tgbot | ssh $(DEPLOY_HOST) $(DOCKER) load

docker_start_remote_tgbot: DEPLOY_HOST?=localhost
docker_start_remote_tgbot: DELTATG_WEBHOOK_URL?=/
docker_start_remote_tgbot: DELTATG_API_TOKEN?=~TOKEN~
docker_start_remote_tgbot: ## tgbot -- copy and run image on remote host (DEPLOY_HOST=…)
	ssh $(DEPLOY_HOST) $(DOCKER) \
	"run \
	--replace \
	--restart unless-stopped \
	--publish 127.0.0.1:17780:17780 \
	--env DELTATG_WEBHOOK_URL="$(DELTATG_WEBHOOK_URL)" \
	--env DELTATG_API_TOKEN="$(DELTATG_API_TOKEN)" \
	--detach \
	--name delta_tgbot \
	delta_tgbot;\
	$(DOCKER) container ls -a --filter name=delta_tgbot"

podman_systemd_remote_tgbot: DEPLOY_HOST?=root@localhost
podman_systemd_remote_tgbot: ## tgbot -- set systemd service to start tgbot via podman after reboot
	ssh $(DEPLOY_HOST) sudo \
	"systemctl link --force /home/delta.qwasa.net/delta/deploy/systemd-podman-delta-tgbot.service;\
	systemctl enable systemd-podman-delta-tgbot.service;\
	systemctl status systemd-podman-delta-tgbot.service;\
	systemctl stop systemd-podman-delta-tgbot.service; sleep 2;\
	systemctl start systemd-podman-delta-tgbot.service"

docker_stop_remote_tgbot: DEPLOY_HOST?=localhost
docker_stop_remote_tgbot:  ## tgbot -- stop docker container (DEPLOY_HOST=…)
	-ssh $(DEPLOY_HOST) '$(DOCKER) container stop -t 1 delta_tgbot; $(DOCKER) container rm delta_tgbot'

copy_files_remote: DEPLOY_HOST?=localhost
copy_files_remote: ## copy all files to remote host (DEPLOY_HOST=…)
	-@git archive --format tar.gz --prefix delta/ master | ssh $(DEPLOY_HOST) 'gunzip -c | tar xv --overwrite'

srcball: OUTPUT?="delta_src_$(TIMESTAMP)_$$(git log --oneline | head -n 1 | sed 's/ .*//').zip"
srcball:
	-git archive --format zip --prefix delta/ master --output "$(OUTPUT)"
	-@ls -lh "$(OUTPUT)"

artwork:  ## make some art
	@rsvg-convert --version || ( echo "rsvg-convert not found, install librsvg2-bin" && exit 1 )
	rsvg-convert -w 512 -h 512 misc/delta-icon.svg -o misc/delta-icon-512x512.png
	rsvg-convert -w 1024 -h 1024 misc/delta-icon.svg -o misc/delta-icon-1024x1024.png

format: ## format python source code
	$(PYTHON) -m black $(SRCFILES)
	$(PYTHON) -m isort $(SRCFILES)

lint:  ## run python linter
	$(PYTHON) -m black --check $(SRCFILES)
	$(PYTHON_LINTER) check $(SRCFILES)
