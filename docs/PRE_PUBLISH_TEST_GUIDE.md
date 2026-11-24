# Pre-publication testing guide

Target: `django-admin-management-fdg==1.0.0`. Use these checks to validate the distribution before uploading it. Use disposable local data and staging deployments, never production data for destructive tests. Commands assume macOS/Linux and Python 3.12 or 3.13. Django 5.2 also supports Python 3.10; Django 6.0 requires Python 3.12+.

## 1. Test the supplied example project

Extract the project ZIP, open Terminal in the directory containing `pyproject.toml`, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . 'Django>=5.2,<5.3'
python -m pip show django-admin-management-fdg Django
python example_project/manage.py check
python example_project/manage.py makemigrations --check --dry-run
python example_project/manage.py test demo --verbosity 2
python example_project/manage.py migrate
python example_project/manage.py createsuperuser
python example_project/manage.py collectstatic --noinput
python example_project/manage.py runserver
```

Open http://127.0.0.1:8000/admin/demo/item/. Expect 15 tests to pass (passed on Django 5.2.19 / Python 3.13 in the release review). Create a disposable item with Add item. Test Manage Items (create, publish, delete, run publishing job), Reports, Existing Page, Item Details, Preview Item, confirmation cancellation and navigation. Open http://127.0.0.1:8000/operations/demo/item/ to test the second AdminSite. Switch light/dark mode and check browser console/network for errors.

Stop the server with Ctrl+C. Repeat in a separate virtual environment with `Django>=6.0,<6.1` and Python 3.12+; then repeat with `Django>=6.1,<6.2` in another environment (Python 3.13 recommended). These are test-series pins, not package dependency limits. A passing 5.2 run does not establish newer-version compatibility.

## 2. Install the wheel in a completely independent project

This is the most important installation test: editable installs can hide missing packaged files. Replace the absolute path below with your extracted package directory. Use a separate terminal and directory, not the package source tree.

```bash
mkdir -p ~/Documents/fdg-management-test
cd ~/Documents/fdg-management-test
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'Django>=5.2,<5.3'
python -m pip install /absolute/path/django-admin-management-fdg/dist/django_admin_management_fdg-1.0.0-py3-none-any.whl
python -m pip check
python -c 'import django_admin_management_fdg as p; print(p.__version__, p.__file__)'
python -m django startproject config .
python manage.py startapp jobs
mkdir -p templates/jobs
```

The printed package path should be inside this project's `.venv`, not the original source checkout.

## 3. Configure the new Django project

In `config/settings.py`, add these entries to the existing `INSTALLED_APPS` list (keep all standard Django apps):

```python
INSTALLED_APPS += [
    'django_admin_management_fdg',
    'jobs',
]
```

After the existing `TEMPLATES` setting, add:

```python
TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Keep `APP_DIRS=True`, default middleware and context processors. The default `config/urls.py` already mounts `admin.site.urls` under `admin/`; no additional URL entries are needed for managed pages or endpoints.

Replace `jobs/models.py` with:

```python
from django.db import models

class JobPost(models.Model):
    title = models.CharField(max_length=150)
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.title
```

Create `jobs/views.py`:

```python
from django.http import JsonResponse
from django.template.response import TemplateResponse
from .models import JobPost


def reports(request):
    return TemplateResponse(request, 'jobs/reports.html', {
        'total': JobPost.objects.count(),
        'published': JobPost.objects.filter(published=True).count(),
    })


def publish(request):
    job = request.fdg_management_object
    job.published = True
    job.save(update_fields=['published'])
    return JsonResponse({'published': True})
```

Replace `jobs/admin.py`:

```python
from django.contrib import admin
from django_admin_management_fdg import (
    ManagementAdminMixin, ManagementPage, ManagementEndpoint,
)
from .models import JobPost
from . import views

@admin.register(JobPost)
class JobPostAdmin(ManagementAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'published')
    search_fields = ('title',)
    list_filter = ('published',)
    management_pages = (
        ManagementPage(name='manage_jobs', label='Manage Jobs',
                       scope='model', group='Operations',
                       template_name='jobs/manage.html',
                       permission='jobs.view_jobpost'),
        ManagementPage(name='reports', label='Reports', scope='model',
                       group='Analytics', view=views.reports,
                       permission='jobs.view_jobpost', order=10),
        ManagementPage(name='preview', label='Preview Job', scope='object',
                       template_name='jobs/preview.html',
                       permission='jobs.view_jobpost', audit=True,
                       endpoints=(ManagementEndpoint(
                           'publish/', 'publish', views.publish,
                           methods=('POST',), permission='jobs.change_jobpost',
                       ),)),
    )
```

## 4. Create the project-level templates

`templates/jobs/manage.html`:

```django
{% extends 'django_admin_management_fdg/base.html' %}
{% block management_content %}
<h1>Manage all jobs</h1>
<p>This is a model-level page. Open Reports to see counts.</p>
{% endblock %}
```

`templates/jobs/reports.html`:

```django
{% extends 'django_admin_management_fdg/base.html' %}
{% block management_content %}
<div class="fdg-dashboard">
  {% include 'django_admin_management_fdg/components/metric.html' with label='Total jobs' value=total only %}
  {% include 'django_admin_management_fdg/components/metric.html' with label='Published' value=published only %}
</div>
{% endblock %}
```

`templates/jobs/preview.html`:

```django
{% extends 'django_admin_management_fdg/base.html' %}
{% load static management_tags %}
{% block management_content %}
<h1>{{ management_object.title }}</h1>
<p>Published: {{ management_object.published|yesno:'Yes,No' }}</p>
{% if perms.jobs.change_jobpost %}
<form id="publish" method="post" action="{% management_endpoint_url 'publish' %}">
  {% csrf_token %}
  <button type="submit">Publish this job</button>
</form>
<p id="status" role="status"></p>
<script type="module">
import { apiFetch, setLoading, showStatus, confirmAction } from "{% static 'django_admin_management_fdg/api.js' %}";
const form = document.getElementById('publish');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!confirmAction('Publish this job?')) return;
  const button = form.querySelector('button');
  setLoading(button, true);
  try {
    await apiFetch(form.action, {method: 'POST'});
    location.reload();
  } catch (error) {
    showStatus(document.getElementById('status'), error.message);
  } finally {
    setLoading(button, false);
  }
});
</script>
{% endif %}
{% endblock %}
```

## 5. Run and verify

```bash
python manage.py makemigrations jobs
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py findstatic django_admin_management_fdg/api.js
python manage.py findstatic django_admin_management_fdg/management.css
python manage.py collectstatic --noinput
python manage.py runserver
```

Open http://127.0.0.1:8000/admin/jobs/jobpost/. Create two unpublished jobs. Manage Jobs and Reports appear on the list; Preview Job appears only on existing change forms. Click Preview Job and publish one record. Confirm the other remains unpublished and Reports shows total 2, published 1. Back navigation should return to the original object on Preview and to the list on Reports. The model route is `/admin/jobs/jobpost/manage/reports/`; for object PK 1 the preview is `/admin/jobs/jobpost/manage-object/1/preview/` and its endpoint ends in `publish/`. Use actual IDs; do not hardcode routes in application templates.

## 6. Verify authorization, CSRF and routing

Create a non-superuser with Staff status and no job permissions in Admin. Sign in using a private browser window. Direct management URLs must be denied (403 for active staff lacking access; anonymous users redirected to login). Grant only `jobs.view_jobpost`: the user can view pages, but not publish. Grant `jobs.change_jobpost`: publishing should succeed with a valid CSRF token. Remove permissions and repeat. A GET to the publish endpoint from an authorized session should return 405. A nonexistent object ID should return 404 for an authorized staff user. Test missing CSRF on a POST with Django's `Client(enforce_csrf_checks=True)`; expect 403. The bundled suite already includes a CSRF test. Confirm no errors are silently treated as success in the browser.

Change the admin mount to `path('dashboard/', admin.site.urls)` in the test project's `config/urls.py`. Restart and verify buttons and navigation use the new prefix automatically. Test with the branding package installed separately using a local/staging configuration; check both themes, admin navigation and all buttons. Do not change the production admin until these pass.

For audit logging, configure the `django_admin_management_fdg.audit` logger at INFO with a handler. It records completed endpoint responses, not denied requests or all database modifications. The example project has a console logger configuration; copy/adapt it if needed.

## 7. Test real applications on staging

Use the migration guide at `../MIGRATION_GUIDE.md` (from this docs directory). First keep existing protected views/URLs and switch only the custom button mechanism. Test Job, Flyer Manifest and Site Notifications independently. Keep their existing API permissions, CSRF, cron secrets, business logic and navigation. Existing named URLs are not wrapped by the package; the original view must secure itself. Check file uploads, editing, deletion, publishing windows and manual cron triggers with disposable data. Avoid invoking production cron jobs from a staging site. When integrating on cPanel, install the tested wheel in the correct Python app environment, run `python manage.py collectstatic --noinput`, and restart the app via its normal deployment mechanism. No package-specific database migrations are needed.

## 8. Release gate

- [ ] All 15 bundled tests pass under Django 5.2, 6.0 and 6.1.
- [ ] Independent wheel installation and sample above pass on both versions.
- [ ] Browser behavior, permissions, CSRF, custom admin prefix and themes pass.
- [ ] Branding and the three real apps pass staging tests.
- [ ] Review MIT license/author and package metadata.
- [ ] Confirm version is `1.0.0` in `pyproject.toml` and `src/django_admin_management_fdg/__init__.py`; confirm README, changelog and development-status classifier agree.
- [ ] Add your actual GitHub repository URL to project metadata if desired; relative docs links work in GitHub/source archive but may not resolve on PyPI's rendered README. Use absolute repository URLs there once known.

From the package source directory, in its build environment:

```bash
python -m pip install --upgrade build twine
rm -rf dist build
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

After checking TestPyPI and testing the rebuilt stable wheel in a fresh environment, upload the same validated distributions to PyPI with `python -m twine upload dist/*`. Do not upload stale distributions or expose tokens. No publication was performed during this review.
