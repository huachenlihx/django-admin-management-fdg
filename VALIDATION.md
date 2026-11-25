# Validation (version 1.0.3)

This file records what has actually been run against this release, and what has not.

## Verified

Review date: 2026-11-24. Environment: Python 3.12.3 on Linux.

| Check | Result |
| --- | --- |
| Bundled test suite (15 tests) on Django 5.2.19 | Pass |
| Bundled test suite (15 tests) on Django 6.0.10 | Pass |
| Bundled test suite (15 tests) on Django 6.1.3 | Pass |
| `manage.py check` | No issues |
| `makemigrations --check --dry-run` | No changes detected |
| `collectstatic` | Pass |
| JavaScript syntax check (`api.js`, `confirm.js`, Node 22, ES modules) | Pass |
| `python -m build` (sdist and wheel) | Pass |
| `twine check` on both distributions | Pass |
| Wheel contents | 6 templates, 3 static files, template tag module present |

The tests cover permissions, CSRF, CRUD endpoints, object scope, navigation, custom AdminSite instances, confirmation attributes and audit logging. Extra manual probes confirmed that view-only staff are refused on write endpoints, that non-staff users are redirected to login, that HEAD requests work on pages, and that button labels are HTML-escaped.

## Not yet verified

- Python 3.10, 3.13 and 3.14. The GitHub Actions matrix in `.github/workflows/tests.yml` covers them; record its result here once it has run.
- Browser behavior (clicks, `fetch` calls, confirmation dialogs, the CSS layout).
- Third-party admin themes (Jazzmin, Grappelli, Unfold and similar).
- Large datasets, concurrency and performance.

## Scope and limits

The package does not replace application-specific authorization, input validation, rate limiting or business rules. Pages added with `url_name` point at existing views, and those views must enforce their own security. Audit logging records completed endpoint responses only and is not a compliance trail.

Django is declared as `Django>=5.2` with no upper bound, so versions newer than those listed above are allowed by the installer but not certified.
