PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
BREW_PACKAGES := sdl2 sdl2_image sdl2_mixer sdl2_ttf

.PHONY: brew-install install run lint clean

brew-install:
	brew install $(BREW_PACKAGES)

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

run:
	$(VENV_PYTHON) main.py

lint:
	$(VENV_PYTHON) -m py_compile main.py src/loves_you/game.py src/loves_you/audio.py src/loves_you/config.py src/loves_you/models.py

clean:
	rm -rf __pycache__ src/loves_you/__pycache__
