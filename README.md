# Django Admin Management FDG

[![PyPI version](https://img.shields.io/pypi/v/django-admin-management-fdg)](https://pypi.org/project/django-admin-management-fdg/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-admin-management-fdg)](https://pypi.org/project/django-admin-management-fdg/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/django-admin-management-fdg)](https://pypi.org/project/django-admin-management-fdg/)

Version **1.0.1**. Add model-level and object-specific management buttons, custom pages and protected endpoints to Django Admin, without database migrations or a DRF dependency. Requires Python 3.10+ and Django 5.2 or newer. The bundled tests pass on Django 5.2, 6.0 and 6.1; see [VALIDATION.md](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/VALIDATION.md) for exact versions and remaining checks. Django has no upper version bound, so releases newer than those listed are permitted by the installer but not certified.

## Features

- Multiple custom management buttons per Django Admin model.
- Model-level and object-specific management pages.
- Automatic URL registration and Admin navigation.
- Support for custom templates, Django views, and existing named URLs.
- Permission-protected API endpoints with CSRF protection.
- Configurable button labels, icons, colors, styles, and ordering.
- Grouped management navigation and optional confirmation dialogs.
- Reusable JavaScript utilities for AJAX requests and status messages.
- Reusable dashboard metric and panel components.
- Optional endpoint audit logging.
- Support for custom AdminSite instances and URL prefixes.
- Django Admin light and dark theme integration.
- No additional database models or migrations.
- No Django REST Framework dependency.

## Documentation

- [Understanding model and object scopes (illustrated guide)](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/docs/scope-guide/SCOPE_GUIDE.md)
- [Testing in a separate Django project](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/docs/PRE_PUBLISH_TEST_GUIDE.md)
- [Migration guide](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/MIGRATION_GUIDE.md)
- [Validation results and limitations](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/VALIDATION.md)
- [MIT License](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/LICENSE)

## Install

Install from [PyPI](https://pypi.org/project/django-admin-management-fdg/):

```bash
pip install django-admin-management-fdg
```

From this source checkout: `python -m pip install -e .`.

Add `django_admin_management_fdg` to `INSTALLED_APPS`. Keep the usual Django admin apps, session/authentication/CSRF/messages middleware and template context processors. Set `APP_DIRS=True` and `DIRS=[BASE_DIR / "templates"]` in the Django template backend to use project-level templates. No package migrations or root URL changes are needed for internally registered routes.

## Quick start

```python
from django.contrib import admin
from django_admin_management_fdg import ManagementAdminMixin, ManagementPage
from .models import JobPost

@admin.register(JobPost)
class JobPostAdmin(ManagementAdminMixin, admin.ModelAdmin):
    management_pages = (
        ManagementPage(name="manage_jobs", label="Manage Jobs", icon="💼",
                       template_name="job/manage_jobs.html",
                       permission="job.view_jobpost"),
        ManagementPage(name="reports", label="Reports", icon="📊",
                       template_name="job/reports.html", order=10),
    )
```

Create `templates/job/manage_jobs.html` and `templates/job/reports.html`:

```html
{% extends 'django_admin_management_fdg/base.html' %}
{% block management_content %}
<h1>My custom page</h1>
<p>Put your own forms, tables and JavaScript here.</p>
{% endblock %}
```

The package places buttons next to the standard Add button. Generated routes follow `<admin-prefix>/<app>/<model>/manage/<name>/`. The base template uses Django's admin theme, includes breadcrumbs and links back to the model and Admin home. Use `management_css` and `management_js` blocks for additional styles and scripts. An independent template is also supported; use `management_parent_url` and `management_admin_home_url` for navigation.

## Built-in templates and how to use them

The package ships six reusable Django templates. They are installed with the package; you do not need to copy them into your project to use them. Keep `APP_DIRS=True` and configure your project template directory as described in [Install](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/README.md#install).

```text
django_admin_management_fdg/templates/
└── django_admin_management_fdg/
    ├── base.html
    ├── buttons.html
    ├── change_list.html
    ├── change_form.html
    └── components/
        ├── metric.html
        └── panel.html
```

| Template (relative to `django_admin_management_fdg/`) | Purpose | How to use |
|---|---|---|
| `base.html` | Admin-themed management page with breadcrumbs, navigation and sibling links | Extend in your own management template |
| `buttons.html` | Renders authorized management buttons, labels, groups, icons, styles and confirmation attributes | Included automatically by the two Admin wrappers; include manually in custom Admin templates if needed |
| `change_list.html` | Adds model-scope buttons to the Admin list page | Used through `ManagementAdminMixin` |
| `change_form.html` | Adds object-scope buttons to the existing object's change page | Used through `ManagementAdminMixin` |
| `components/metric.html` | Displays a label, value and optional description | Include in a dashboard or management page |
| `components/panel.html` | Displays a heading and description | Include in a dashboard or management page |

### 1. `base.html`: create a management page

Create your own template under the project-level `templates/` directory, for example `templates/job/manage_jobs.html`. Do not edit the installed package's base template for ordinary page customization.

```django
{% extends "django_admin_management_fdg/base.html" %}
{% load static %}

{% block management_css %}
    <link rel="stylesheet" href="{% static 'job/manage.css' %}">
{% endblock %}

{% block management_js %}
    <script defer src="{% static 'job/manage.js' %}"></script>
{% endblock %}

{% block management_content %}
    <h2>Manage jobs</h2>
    <p>Add your forms, tables, reports and API-driven operations here.</p>
{% endblock %}
```

The CSS and JavaScript blocks are optional. If you use the example assets, create `job/static/job/manage.css` and `job/static/job/manage.js` in your app. Scripts placed in `management_js` are loaded in the Admin document head; use `defer` for scripts that need the page DOM.

Register the template in your `ManagementAdminMixin` subclass:

```python
ManagementPage(
    name="manage_jobs",
    label="Manage Jobs",
    scope="model",
    template_name="job/manage_jobs.html",
    permission="job.view_jobpost",
)
```

The base extends `admin/base_site.html`, loads the package stylesheet and confirmation script, and supplies navigation. Its relevant template context is:

| Variable | Purpose |
|---|---|
| `title` | Management page title |
| `opts` | Django model metadata |
| `management_admin_home_url` | Admin home URL |
| `management_app_url` | Admin application list URL |
| `management_parent_url` | Parent changelist or object change form URL |
| `management_page` | Current management page configuration |
| `management_siblings` | Permitted sibling management links of the same scope |
| `management_object` | Selected instance for an object-scope page |

For an object page you can use `{{ management_object.pk }}` and the instance's fields in `management_content`. For a custom view returning an unrendered `TemplateResponse`, the package supplies its context automatically; for an eager `render()` response, merge `request.fdg_management_context` before rendering. A page reached through `url_name` does not receive these variables automatically: its own view must supply context, navigation and permissions. An independent existing page can instead extend `admin/base_site.html` and use its AdminSite's `each_context(request)`.

### 2. `buttons.html`: render management links in a custom Admin template

Normally the mixin renders this partial automatically. It consumes `fdg_management_buttons`, a collection of button entries containing `url` and `page`. It renders `<li>` elements, so include it inside the Admin object-tools list, not as a standalone page. Button appearance and confirmation text come from the `ManagementPage` configuration, not from hardcoded links in your template.

If you already override `change_list_template`, you can preserve your template and add the partial:

```django
{% extends "admin/change_list.html" %}

{% block object-tools-items %}
    {% include "django_admin_management_fdg/buttons.html" %}
    {{ block.super }}
{% endblock %}
```

For a custom object change form, extend `admin/change_form.html` instead and use the same block. Preserve `{{ block.super }}` to retain Django's standard tools. Do not include the partial twice. Button visibility is not a replacement for server-side authorization.

### 3. `change_list.html`: model-level buttons

The package wrapper extends the template specified by `fdg_management_changelist_base`, defaulting to `admin/change_list.html`, and includes the buttons partial in `object-tools-items`.

With the mixin and `scope="model"`, no explicit template override is normally required. To retain a custom underlying changelist, set this on your ModelAdmin:

```python
management_changelist_base = "job/admin/custom_change_list.html"
```

The custom base must extend a normal Admin changelist, not the package's wrapper. Remove a competing `change_list_template` override if you choose this approach. Keep its `object-tools-items` block cooperative and do not add the buttons partial there again.

### 4. `change_form.html`: object-level buttons

This wrapper uses `fdg_management_changeform_base`, defaulting to `admin/change_form.html`. Define an object-scope page to add a button to an existing record's change form:

```python
ManagementPage(
    name="preview",
    label="Preview Job",
    scope="object",
    template_name="job/preview.html",
    permission="job.view_jobpost",
)
```

For example, `templates/job/preview.html`:

```django
{% extends "django_admin_management_fdg/base.html" %}

{% block management_content %}
    <h2>{{ management_object.title }}</h2>
    <p>Job ID: {{ management_object.pk }}</p>
{% endblock %}
```

If you have a custom underlying change form, set:

```python
management_changeform_base = "job/admin/custom_change_form.html"
```

The custom base must extend a normal Admin change form, not the package wrapper. Remove a competing `change_form_template` override when using this approach. Alternatively, keep your direct override and include the buttons partial as in section 2. Object-scope buttons are for saved objects, not add forms.

### 5. `components/metric.html`: display a metric

Include this component within your management page. It accepts `label`, `value` and optional `description`.

```django
{% include "django_admin_management_fdg/components/metric.html" with label="Total jobs" value=total_jobs description="All job postings" only %}
```

`value` is supplied by your view; the component does not query the database or calculate statistics. The `only` keyword isolates the included template's context to the supplied arguments.

### 6. `components/panel.html`: display a text panel

This component accepts `heading` and `description`. It is a simple text panel, not a block-based container for arbitrary nested HTML.

```django
{% include "django_admin_management_fdg/components/panel.html" with heading="Publishing status" description="Review scheduled jobs before publishing." only %}
```

### Complete dashboard example

In `job/views.py`, assuming your `JobPost` model has an `is_published` database field:

```python
from django.template.response import TemplateResponse
from .models import JobPost


def reports(request):
    return TemplateResponse(
        request,
        "job/reports.html",
        {
            "total_jobs": JobPost.objects.count(),
            "published_jobs": JobPost.objects.filter(is_published=True).count(),
        },
    )
```

Adapt the query to your actual model fields and restrict the queryset to records the user may view where required. Register the view in your ModelAdmin:

```python
ManagementPage(
    name="reports",
    label="Reports",
    scope="model",
    view=views.reports,
    permission="job.view_jobpost",
)
```

Import `views` from your app in `admin.py`. Use `view` instead of `template_name` here, not both.

Create `templates/job/reports.html`:

```django
{% extends "django_admin_management_fdg/base.html" %}

{% block management_content %}
    <div class="fdg-dashboard">
        {% include "django_admin_management_fdg/components/metric.html" with label="Total jobs" value=total_jobs only %}
        {% include "django_admin_management_fdg/components/metric.html" with label="Published" value=published_jobs only %}
        {% include "django_admin_management_fdg/components/panel.html" with heading="Status" description="Review publishing activity here." only %}
    </div>
{% endblock %}
```

The package stylesheet loaded by `base.html` supplies the component styles. If using the components in an independent template, load `static` and include `django_admin_management_fdg/management.css` yourself; the components rely on Admin theme variables.

### Template discovery and local testing

From a Django project with the package installed and configured:

```bash
python manage.py check
python manage.py shell -c "from django.template.loader import get_template; print(get_template('django_admin_management_fdg/base.html').origin)"
python manage.py findstatic django_admin_management_fdg/management.css django_admin_management_fdg/confirm.js
python manage.py runserver
```

Open the model's Admin list page, test the model-level buttons, open a saved object and test its object-level buttons, then verify breadcrumbs, Back navigation, dashboard components and both Admin themes. In production, run `python manage.py collectstatic --noinput` as part of normal deployment. Changing only HTML templates does not require migrations or collecting static files again. If modifying the package itself, an editable install uses the updated source templates; rebuild the wheel for distribution testing.


## Three page modes

Provide exactly one of `template_name`, `view`, or `url_name`.

- `template_name`: automatically rendered with Admin context; GET/HEAD only.
- `view`: a Django callable or class-based view via `.as_view()`; GET/HEAD only. Unrendered `TemplateResponse` receives the package's context automatically. For `render()` or eager responses, explicitly merge `request.fdg_management_context` before rendering. Existing context values override package defaults.
- `url_name`: a pre-existing reversible named URL with no required arguments. This only adds the link. The destination and its API endpoints must enforce their own authentication, permissions, CSRF, and HTTP methods. Existing pages own their navigation. Do not treat link visibility as security.

The mixin must precede `admin.ModelAdmin` in the inheritance list. Preserve cooperative `super()` calls in overrides. `management_pages` is static per registered model; do not vary it by request because the URLconf is built independently of requests.

## Endpoints and custom views

```python
from django_admin_management_fdg import ManagementPage, ManagementEndpoint
from .views import ManageJobsView, create_job, run_cron

management_pages = (
    ManagementPage(name="jobs", label="Manage Jobs", view=ManageJobsView.as_view(),
                   permission="job.view_jobpost", endpoints=(
        ManagementEndpoint("create/", "create", create_job,
                           methods=("POST",), permission="job.add_jobpost"),
        ManagementEndpoint("run-cron/", "run_cron", run_cron,
                           methods=("POST",), permission="job.can_run_job_cron"),
    )),
)
```

Endpoints are registered relative to their page and can use Django converters, e.g. `edit/<uuid:pk>/`. Reverse names are generated internally; do not hardcode them. In a management template:

```html
{% load static management_tags %}
<form id="job-form" data-url="{% management_endpoint_url 'create' %}">
  {% csrf_token %}
  <input name="title" required>
  <button type="submit">Create</button>
</form>
<script type="module">
import { apiFetch } from "{% static 'django_admin_management_fdg/api.js' %}";
const form = document.getElementById('job-form');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await apiFetch(form.dataset.url, {method: 'POST', body: new FormData(form)});
    location.reload();
  } catch (error) { alert(error.message); }
});
</script>
```

For a parameterized route use `{% management_endpoint_url 'edit' pk=object.pk %}`. For JSON requests set `Content-Type: application/json` and serialize the body yourself. The helper supports same-origin requests only; it prefers the rendered CSRF form token and otherwise uses the default `csrftoken` cookie. Include `{% csrf_token %}` for custom cookie names, session-backed tokens or HTTP-only cookies. It rejects redirects (including expired login redirects) and throws on HTTP errors. It does not implement automatic retries. Optional utilities: `getCsrfToken`, `setLoading`, `showStatus`, `confirmAction`.

## Configuration reference

| ManagementPage property | Meaning |
|---|---|
| name | Unique lowercase identifier (letters/digits/underscore, starts with letter) |
| label | Button and page title |
| template_name / view / url_name | Exactly one destination |
| permission | Additional Django permission (`app.codename`), optional |
| icon / tooltip | Optional escaped text |
| color / text_color | Optional six-digit hex colors |
| button_style | `pill` (native default), `rounded`, `square` |
| order | Integer sorting key; equal values retain declaration order |
| endpoints | Tuple of `ManagementEndpoint` configurations |
| scope | `model` (default) or `object` |
| group | Optional button/navigation group |
| confirmation | Optional browser confirmation text |
| audit | Enable endpoint activity logging (default `False`) |

`ManagementEndpoint(route, name, view, methods=("POST",), permission=None)` registers an additional protected callable. Endpoint names and literal routes must be unique within the page. Avoid overlapping converter patterns; Django resolves in declaration order.

## Permissions and security

Internally registered pages and endpoints require the AdminSite's permission (active staff by default), model view or change permission, and the optional page permission. Endpoints additionally enforce their own optional permission and HTTP method allowlist. CSRF is enforced even when a supplied callable declares itself exempt. Admin routes use the AdminSite wrapper and are not cached by default. Do not use GET for mutations. The package does not decide custom object-level authorization, input validation, rate limits, transaction boundaries, durable audit retention, or business rules: these belong in your application. Never pass cron credentials to browser JavaScript. Use protected POST endpoints that call server-side publishing services or management commands. Avoid exposing duplicate unprotected routes.

An endpoint with no `permission=` is available to every user who can open its page (staff access plus model view or change permission). Set an explicit `permission` on every endpoint that creates, changes or deletes data.

To customize permission policy, override `has_management_permission(request, page, obj=None)` carefully, retaining staff and model authorization unless you have a deliberate alternative. Buttons and internal routes use this same hook. Existing named URLs remain independently protected.

## Existing admin templates / branding

The package uses an opt-in changelist template, not a global override. To preserve an existing custom changelist set `management_changelist_base = "path/to/original.html"` and remove the old `change_list_template` override. The original must extend a normal Admin changelist and must not extend the package changelist (avoid recursion). Alternatively keep your existing `change_list_template` and explicitly include `{% include 'django_admin_management_fdg/buttons.html' %}` inside its `object-tools-items` block, preserving `{{ block.super }}`. Remove old duplicate buttons. Custom AdminSite names and URL prefixes are supported by reversing instance names. Branding extensions that customize `admin/base_site.html` should compose normally; actual compatibility with third-party themes must be tested.

## Example project and tests

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python example_project/manage.py migrate
python example_project/manage.py createsuperuser
python example_project/manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/demo/item/` and try Manage Items, Reports, Existing Page. The example supports creating, publishing, deleting and manually running a bulk publishing operation. A second admin instance is at `/operations/`. Example settings and secret are development-only. The example uses SQLite; the reusable package has no database tables.

```bash
python example_project/manage.py check
python example_project/manage.py test demo --verbosity 2
python example_project/manage.py collectstatic --noinput
```

On cPanel, add the package to your requirements, install in the application's environment, run `collectstatic --noinput` and restart the deployed application. Use your normal production WSGI/ASGI deployment; do not run Django's development server in production.

## Build and publish

```bash
python -m pip install --upgrade build twine
rm -rf dist build
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
# After validating the TestPyPI distribution:
python -m twine upload dist/*
```

The manual GitHub publishing workflow uses PyPI Trusted Publishing; configure the matching repository, workflow and `pypi` environment in PyPI first. Never commit API tokens. Review the license and author metadata before publishing.

See [MIGRATION_GUIDE.md](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/MIGRATION_GUIDE.md) for how to move an existing Admin button, custom page or set of AJAX routes onto this package.

## Extended functionality in 1.0

Existing model-level
configurations still default to `scope="model"`.

### Object-specific pages

Add a page to `management_pages` with `scope="object"`. Its button appears on
existing object change forms (not on add forms or the changelist). For example:

```python
ManagementPage(
    name="details", label="Details", scope="object",
    template_name="demo/item_details.html", permission="demo.view_item",
    group="Item", confirmation="Open details?", audit=True,
)
```

The package uses `ModelAdmin.get_object()` (and therefore its queryset) to
resolve the quoted object ID. It checks `has_view_or_change_permission(request,
obj)` and any explicit page and endpoint permissions. For custom views and
endpoints the resolved instance is `request.fdg_management_object`. Do not
trust an alternate object ID supplied by the client. Add explicit mutation
permissions to every write endpoint, including object-level permission checks
where your application needs them. The template receives `management_object`;
`management_parent_url` points back to its change form. The
`management_endpoint_url` tag automatically includes the object ID.
Object pages cannot use `url_name`; external routes remain model-level only.
Override `has_management_permission(self, request, page, obj=None)` for custom
policies; existing two-argument overrides continue to work for model pages.

### Groups, navigation and confirmation

`group="Operations"` labels related buttons and groups sibling navigation on
managed pages. The sibling navigation only lists permitted pages of the same
scope. `confirmation="Continue?"` enables an optional browser confirmation
when following a link. It is a UX convenience, not authorization. For destructive
API actions use the optional `confirmAction()` JS utility and enforce server-side
permissions and CSRF protection independently. Custom changelist and change form
templates must include the package's buttons partial, or set
`management_changelist_base` and `management_changeform_base` to your own base
paths. If you override admin template attributes directly, you must include the
partial yourself.

### Audit logging

Set `audit=True` on a managed page to emit INFO records for endpoint responses
through `django_admin_management_fdg.audit`. Configure Django LOGGING with a
handler and retention policy. Extra fields are `fdg_actor`, `fdg_model`,
`fdg_object`, `fdg_page`, `fdg_endpoint`, `fdg_method`, and `fdg_status`.
The package does not store request bodies, tokens, or audit database rows. This
records returned endpoint responses only, not denied requests, unhandled
exceptions or changes made outside these endpoints; it is not a compliance audit
trail. External views are responsible for their own audit logging.

### Dashboard components

```django
<div class="fdg-dashboard">
  {% include 'django_admin_management_fdg/components/metric.html' with label='Items' value=item_count only %}
  {% include 'django_admin_management_fdg/components/panel.html' with heading='Status' description='Ready' only %}
</div>
```

These components use admin theme variables. See the example object's Details
and Preview buttons for a working integration example to test locally.

### Release verification

Version `1.0.1` is a documentation-only patch release on top of `1.0.0`. See [VALIDATION.md](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/VALIDATION.md) for the checks that have been run and those still outstanding. Before each release, run the CI matrix, then run `python -m twine check dist/*`. The manual publish workflow blocks prerelease versions.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/huachenlihx/django-admin-management-fdg/blob/main/LICENSE) file for details.
