TESTS = test_builder test_client test_render test_impl test_simulator

test:
	nose2 -s test -A !slow -C -v ${TESTS}

test-all:
	nose2 -s test -C -v ${TESTS}

typecheck:
	mypy pyecsca --ignore-missing-imports

codestyle:
	flake8 --ignore=E501,F405,F403,F401,E126 pyecsca

.PHONY: test test-all typecheck codestyle