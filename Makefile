PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
BREWFILE ?= Brewfile

.PHONY: brew-install install run lint clean

brew-install:
	brew bundle --file $(BREWFILE)

install:
	[ -d $(VENV) ] || $(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

run:
	$(VENV_PYTHON) main.py

lint:
	$(VENV_PYTHON) -m py_compile main.py src/loves_you/game.py src/loves_you/audio.py src/loves_you/config.py src/loves_you/models.py

clean:
	rm -rf __pycache__ src/loves_you/__pycache__ .pytest_cache .mypy_cache
