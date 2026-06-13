.PHONY: venv install test build clean

venv:
	@rm -rf .venv
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@echo "Run 'source .venv/bin/activate' to enable the environment"

install:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

build:
	bash scripts/build.sh all

build-layer:
	bash scripts/build.sh shared-layer

build-api:
	bash scripts/build.sh api

build-send-email:
	bash scripts/build.sh send-email

clean:
	rm -rf dist/
