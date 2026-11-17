# Contributing

Install Python 3.10 or newer and run `python -m pip install -e .`.
Install pre-commit in your development environment and run `pre-commit install`.
Before opening a pull request, run `pre-commit run --all-files` and
`python -m unittest discover -s tests`.

Use synthetic fixtures for simulations. Include the seed and step count when
reporting unexpected behavior. Keep changes to evidence schemas compatible
with existing reports or document a schema-version migration. Report security
issues using the [security policy](../SECURITY.md).
