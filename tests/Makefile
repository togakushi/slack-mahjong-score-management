prospector:
	@uv run prospector -W mccabe ..

# --
.PHONY: docs
docs:
	rm -rf docs/html
	uv run pdoc -d google --output-dir docs/html --logo '' --logo-link '' *.py libs cls integrations tests

# --
config_file = ../config.ini
a.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-All.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-FileGeneration.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-LastMonth.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-OutOfScope.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-Report.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-ThisMonth.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-anonymous.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-groupby.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-help.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-individual.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-rating.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-team.ini:
	PYTHONPATH=.. uv run ./test.py -c $(config_file) -t ./test_case/$@

test-saki:
	PYTHONPATH=.. uv run ./test.py -c ./test_data/saki.ini -t ./test_data/test_pattern01.ini
