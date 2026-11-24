# Migration guide

This guide explains how to move an existing Django Admin customization (a hand-written button, a hardcoded URL, a custom page) onto `django-admin-management-fdg`. Migrate one ModelAdmin at a time, and test in staging first.

## Choose a migration level

| Level | What you keep | What you change | Risk |
| --- | --- | --- | --- |
| 1. Button only | Existing views, URLs and templates | Replace the custom button wiring with `ManagementPage(url_name=...)` | Lowest |
| 2. Managed page | Existing business logic | Serve the page through the package (`template_name=` or `view=`) | Medium |
| 3. Managed page and endpoints | Business logic only | Move AJAX or POST routes into `ManagementEndpoint` | Highest |

Start at level 1. Move up only when you want the package to handle permissions, CSRF, navigation and audit logging for you.

## Level 1: replace only the button

Before, a typical ModelAdmin overrides `change_list_template` and injects a hardcoded URL:

```python
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    change_list_template = "reports/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["upload_page_url"] = "/reports/upload-page/"
        return super().changelist_view(request, extra_context=extra_context)
```

After, put the mixin first and declare the button:

```python
from django_admin_management_fdg import ManagementAdminMixin, ManagementPage

@admin.register(Report)
class ReportAdmin(ManagementAdminMixin, admin.ModelAdmin):
    management_pages = (
        ManagementPage(
            name="upload",
            label="Upload Page",
            icon="🖼️",
            url_name="reports_upload_page",      # your existing named URL
            permission="reports.can_upload",
        ),
    )
```

Then:

1. Add `"django_admin_management_fdg"` to `INSTALLED_APPS`.
2. Remove the old `change_list_template`, the context injection and any button-only CSS, but only after checking they have no other job.
3. If you still need your own changelist template, keep it and set `management_changelist_base = "reports/change_list.html"` (and `management_changeform_base` for the change form) so the package extends your template.

Important points for `url_name` pages:

- They are model-scope only. `scope="object"` with `url_name` is rejected.
- The package only shows or hides the button. **Your existing view must still enforce its own access checks.**
- The name is resolved with `reverse()`. If your URLconf is namespaced, use the qualified name, for example `"admin:reports_report_upload"`. That form assumes the default AdminSite.
- `audit=True` is not allowed with `url_name`; the existing view is responsible for its own audit logging.

## Level 2: let the package serve the page

Use a template that extends the package base:

```python
ManagementPage(name="reports", label="Reports",
               template_name="reports/dashboard.html",
               permission="reports.view_report")
```

```django
{% extends "django_admin_management_fdg/base.html" %}
{% block management_content %}
  <h1>Reports</h1>
{% endblock %}
```

Or use a callable or class-based view. The package injects admin context as `request.fdg_management_context`, and merges it into any unrendered `TemplateResponse`:

```python
ManagementPage(name="reports", label="Reports", view=ReportDashboardView.as_view())
```

## Level 3: move endpoints into the page

If your page makes POST, PATCH or DELETE calls, declare them as endpoints:

```python
ManagementPage(
    name="manage", label="Manage", view=views.manage, permission="reports.view_report",
    audit=True,
    endpoints=(
        ManagementEndpoint("create/", "create", views.create, permission="reports.add_report"),
        ManagementEndpoint("delete/<int:pk>/", "delete", views.delete,
                           methods=("DELETE",), permission="reports.delete_report"),
    ),
)
```

In templates, resolve the generated URLs with the tag:

```django
{% load management_tags %}
{% management_endpoint_url 'delete' pk=item.pk %}
```

Before removing an old route:

- Update every template `{% url %}` tag, `reverse()` call and JavaScript URL that referenced it.
- Check that HTTP methods match what the view expects. Endpoints default to `POST` only.
- Preserve URL converters (for example `<uuid:pk>`).
- Set an explicit `permission=` on every endpoint that changes data. An endpoint with no permission is available to any user who can open its page.

## Object-scope pages

For a button that acts on one saved record, use `scope="object"`. The button appears on the change form, not on the add form or changelist. Your view or template receives `request.fdg_management_object` and `management_object`.

## Do not change

Leave these alone during a migration:

- Public-facing URLs and scheduled or cron endpoints.
- Existing authorization logic that lives in your views.
- Models, migrations and business logic.

## Checklist

- [ ] The mixin comes before `admin.ModelAdmin` in the class bases.
- [ ] `reverse()` confirms the real URL names and namespaces in your project.
- [ ] Authorized and unauthorized users were tested, including direct requests to every endpoint.
- [ ] CSRF behavior was tested (a missing token should return 403).
- [ ] All existing create, edit, delete and publish operations still work.
- [ ] Original navigation, styling, language and time zone behavior are unchanged.
- [ ] `collectstatic` was run and the server restarted after deployment.
