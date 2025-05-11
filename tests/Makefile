mypy:
	@mypy --check-untyped-defs $(shell git ls-files '../*.py')

pylint:
	@pylint $(shell git ls-files '../*.py')

prospector:
	@prospector -W mccabe ..

# --
.PHONY: docs
docs:
	rm -rf docs/html
	pdoc -d google --output-dir docs/html --logo '' --logo-link '' *.py libs cls tests

# --
config_file = ../config.ini
a.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-All.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-FileGeneration.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-LastMonth.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-OutOfScope.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-Report.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-ThisMonth.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-anonymous.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-groupby.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-help.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-individual.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-rating.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-team.ini:
	PYTHONPATH=.. ./test.py -c $(config_file) -t ./test_case/$@

test-saki:
	PYTHONPATH=.. ./test.py -c ./test_data/saki.ini -t ./test_data/test_pattern01.ini
