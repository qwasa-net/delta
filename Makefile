#
SHELL := /bin/bash
TIMESTAMP := $(shell date +"%Y%m%d-%H%M")

#
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))
HOME_PATH := $(MAKEFILE_DIR)
ENV_PATH ?= $(HOME_PATH)/_env
MENAME ?= $(shell basename "$(MAKEFILE_DIR)")

# python sorce code linter
PYLINT ?= $(ENV_PATH)/bin/pylint
PYLINT_FLAGS ?= -sy --rcfile=.pylintrc
PYTHON_LINTER ?= $(PYLINT) $(PYLINT_FLAGS)
PYTHON_LINTER_FILES := $(wildcard */*.py)

.PHONY: help

help:
	-@grep -E "^[a-z_0-9]+:" "$(strip $(MAKEFILE_LIST))" | grep '##' | sed 's/:.*##/## —/ig' | column -t -s '##'

test:  ## run unittests
	$(ENV_PATH)/bin/python -m unittest --verbose --failfast

test_run_commander:  ## run test for delta commander
	$(ENV_PATH)/bin/python clients/delta_commander.py -v data/dictionary-test.xml --allow-shell --say "what time is it?"

pylint: $(patsubst %.py,%.pylint,$(PYTHON_LINTER_FILES))  ## run python linter

%.pylint:
	$(PYTHON_LINTER) $*.py
