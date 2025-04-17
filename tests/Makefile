mypy:
	@mypy --check-untyped-defs $(shell git ls-files '../*.py')

pylint:
	@pylint $(shell git ls-files '../*.py')

prospector:
	@prospector -W mccabe ..

test-a:
	@echo ">>> テスト"
	PYTHONPATH=.. ./test.py -c config.ini -t ./test_case/a.ini

test-saki:
	PYTHONPATH=.. ./test.py -c ./test_data/saki.ini -t ./test_data/test_pattern01.ini
