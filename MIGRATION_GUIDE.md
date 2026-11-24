# Migration notes: United Supermarket Adelaide

This is a generic new library, not a modification of the production apps. Keep existing business logic and URL protections. Test in staging first.

## Flyer Manifest

`FlyerFileAdmin` currently sets `change_list_template`, injects `upload_page_url` via `changelist_view`, and uses a hardcoded `/flyer-manifest/upload-page/`. Replace just the button wiring with:

```python
class FlyerFileAdmin(ManagementAdminMixin, admin.ModelAdmin):
    management_pages = (
        ManagementPage(name="staff_upload", label="Staff Upload Page", icon="🖼️",
                       url_name="flyer_upload_page",
                       permission="flyer_manifest.can_upload_flyer"),
    )
    # Keep existing list_display, filters, fields and other methods.
```

Remove old button-specific template override/context/CSS only after checking it has no other responsibilities. Existing named routes and upload/edit/reorder/cron views stay intact. If the root project namespaces this URLconf, use the actual qualified URL name. Preserve the separate `flyer_manifest.can_run_flyer_manifest_cron` check and independently verify staff-only access on existing routes.

## Site Notifications

`SiteNotificationAdmin` currently injects `manage_page_url` using `/site-notifications/manage/`. Configure:

```python
management_pages = (
    ManagementPage(name="notifications", label="Manage Notifications", icon="🔔",
                   url_name="notifications_manage",
                   permission="site_notifications.can_manage_notifications"),
)
```

Add the mixin before ModelAdmin. Keep the existing `save_model`, role display, date/time logic and all existing API and cron permission checks. The named URL approach preserves the existing page design and current AJAX URLs; add navigation to that template yourself or migrate it to an internal page later.

## Jobs

`JobPostAdmin` currently registers `manage/`, `manage/create/`, `manage/edit/<uuid:pk>/`, `manage/delete/<uuid:pk>/`, and `manage/run-cron/` in `get_urls()`. It also has app-level aliases in `job.urls`. For the lowest-risk initial migration retain its existing `get_urls` and views, remove the old button wiring and add:

```python
management_pages = (
    ManagementPage(name="jobs", label="Manage Jobs", icon="💼",
                   url_name="admin:job_jobpost_manage",
                   permission="job.can_upload_job"),
)
```

This assumes the default AdminSite namespace. Preserve existing protection and `job.can_run_job_cron`. For a later full migration use `view=JobManagePageView.as_view()` and `ManagementEndpoint` for the create/edit/delete/run-cron views. Update all existing template URL tags, view URL reversals and JavaScript URL references to the new generated names before removing old routes. Do not change public job application or scheduled cron URLs as part of this migration. Verify HTTP methods against the existing views and preserve UUID converters.

## Common checklist

- Add package and mixin imports; keep original models, migrations and business logic.
- Confirm existing project URL namespaces with `reverse()`.
- Test authorized and unauthorized users, direct endpoint requests, CSRF, and all existing CRUD and publishing operations.
- Test original navigation, styling, language and timezone behavior.
- Run collectstatic and restart after deployment.
