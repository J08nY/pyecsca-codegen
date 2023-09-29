TESTS = test_builder test_client test_commands test_render test_impl test_simulator

test:
	pytest -s -m "not slow" --cov=pyecsca.codegen test/test_simulator

test-all:
	pytest --cov=pyecsca.codegen

typecheck:
	mypy pyecsca --ignore-missing-imports

codestyle:
	flake8 --ignore=E501,F405,F403,F401,E126 pyecsca

.PHONY: test test-all typecheck codestyle