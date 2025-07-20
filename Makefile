.PHONY: venv
venv:
	## Create a virtual environment
	@rm -rf .venv
	@echo "Creating virtualenv ..."
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@echo
	@echo "Run 'source .venv/bin/activate' to enable the environment"


.PHONY: install
install:
	## Install python dependencies
	pip install -r requirements.txt
	pip install -r lambdas/lambda_test/requirements.txt