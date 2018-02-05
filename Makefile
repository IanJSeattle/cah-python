test: *.py test/*.py
	test/test.py

lint: *.py
	mypy *.py
	pylint *.py

all: test lint
