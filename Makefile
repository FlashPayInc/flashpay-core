LINT_PATHS = flashpay/ manage.py
ISORT_PARAMS = --ignore-whitespace  $(LINT_PATHS)
ISORT_CHECK_PARAMS = --diff --check-only
BLACK_CHECK_PARAMS = --diff --color --check

lint:
	isort $(ISORT_PARAMS) $(ISORT_CHECK_PARAMS)
	flake8 $(LINT_PATHS)
	mypy $(LINT_PATHS) --install-types --non-interactive
	black $(BLACK_CHECK_PARAMS) ./

run-dev:
	python manage.py runserver

test:
	pytest --cov -xs