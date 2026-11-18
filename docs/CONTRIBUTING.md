# Contributing

Install Python 3.10 or newer and run `python -m pip install -e .`.
Install pre-commit in your development environment and run `pre-commit install`.
Before opening a pull request, run `pre-commit run --all-files` and
`python -m unittest discover -s tests`.

Use synthetic fixtures for simulations. Include the seed and step count when
reporting unexpected behavior. Keep changes to evidence schemas compatible
with existing reports or document a schema-version migration. Report security
issues using the [security policy](../SECURITY.md).

## Find a first contribution

1. Run [the quickstart](../README.md#run-it-locally) and follow the blocked finding
   through remediation and verification. Report any step that is unclear.
2. Choose a small, reproducible improvement. Useful entry points include
   synthetic fixtures, CI evidence producer examples, accessibility in the
   operator console, and tests for malformed evidence.
3. For a new integration, open a proposal with a sample of the normalized
   input, the expected report or exit code, and how someone can verify it locally.
4. Keep the change focused and include the validation evidence in the pull
   request. Document new behavior where users first encounter it.

Use the [issue templates](https://github.com/bijit-ghosh/CyberOps/issues/new/choose)
for bugs and proposals.
