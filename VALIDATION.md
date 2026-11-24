# Version 1.0.0 validation

The maintainer reports testing the whole project and requested promotion to 1.0.0. Detailed local test logs and a compatibility matrix were not supplied.

## Independently verified

- Python 3.13.5 / Django 5.2.19: all 15 bundled tests passed, including permissions, CSRF, CRUD, object scope, navigation, custom AdminSite and audit logging. Django and its pure-Python dependencies were recovered from the uploaded virtual environment for these checks; the virtual environment is not shipped.
- Django system checks, migration consistency, static collection, Python syntax and JavaScript syntax checks passed.
- Both distributions built successfully; all 15 tests also passed using the installed 1.0.0 wheel in an isolated target directory. Wheel metadata, six HTML templates, three static assets, source documentation and four illustrations were verified.
- Release metadata, documentation and packaging reviewed; runtime source preserved apart from the version constant.

## Remaining checks

- Django 6.0, 6.1 and the full Python/Django CI matrix were not independently executed.
- Browser testing, third-party branding compatibility and the three production-app staging integrations were not independently reproduced.
- Twine is not available in the review environment; run `python -m twine check dist/*` locally before upload. The GitHub publishing workflow also runs tests and Twine checks.
- The actual repository URL was not supplied; README documentation links remain relative and may not work in the PyPI rendering. Use absolute repository links when known.

The package does not replace application-specific authorization, input validation or business logic. Existing named URLs must independently enforce security. No upload to PyPI or TestPyPI has been performed.

## Dependency update review

The package now declares `Django>=5.2` with no upper limit and `requires-python = ">=3.10"`. All 15 source tests passed again on Python 3.13.5 / Django 5.2.19; system checks and migration consistency passed. Django 6.1.3 could not be installed from the available package index in the review environment; compatibility remains unverified. CI now includes a Django 6.1 matrix entry.
- Rebuilt wheel and source distribution, both declaring the new dependency. All 15 tests passed against the rebuilt installed wheel; its import location and metadata were checked. Static collection, Python/JavaScript syntax and packaged asset checks passed again.
