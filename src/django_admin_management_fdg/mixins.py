"""Integrate management pages without globally overriding Admin templates."""
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.http import HttpResponseNotAllowed, Http404
from django.contrib.admin.utils import quote, unquote
import logging

logger = logging.getLogger("django_admin_management_fdg.audit")
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie


class ManagementAdminMixin:
    management_pages = ()
    change_list_template = "django_admin_management_fdg/change_list.html"
    change_form_template = "django_admin_management_fdg/change_form.html"
    management_changeform_base = "admin/change_form.html"
    management_changelist_base = "admin/change_list.html"

    def get_management_pages(self):
        pages = tuple(self.management_pages)
        if len({p.name for p in pages}) != len(pages):
            raise ImproperlyConfigured("Duplicate management page names")
        return sorted(pages, key=lambda p: p.order)

    def has_management_permission(self, request, page, obj=None):
        return (self.admin_site.has_permission(request)
                and self.has_view_or_change_permission(request, obj)
                and (not page.permission or request.user.has_perm(page.permission)))

    def management_url_name(self, page, endpoint=None):
        opts = self.model._meta
        # Double underscore separates page and endpoint; length prefix avoids collisions.
        name = f"{opts.app_label}_{opts.model_name}_fdg_{len(page.name)}_{page.name}"
        return f"{name}_{endpoint.name}" if endpoint else name

    def _reverse(self, name, **kwargs):
        return reverse(f"{self.admin_site.name}:{name}", kwargs=kwargs or None)

    def management_url(self, page, obj=None):
        if page.url_name:
            return reverse(page.url_name, current_app=self.admin_site.name)
        return self._reverse(self.management_url_name(page), **({"object_id": quote(obj.pk)} if page.scope == "object" else {}))

    def management_context(self, request, page, obj=None):
        opts = self.model._meta
        request.current_app = self.admin_site.name
        return {
            **self.admin_site.each_context(request),
            "opts": opts,
            "title": page.label,
            "management_page": page,
            "management_object": obj,
            "management_object_id": quote(obj.pk) if obj is not None else None,
            "management_admin_home_url": self._reverse("index"),
            "management_parent_url": self._reverse(f"{opts.app_label}_{opts.model_name}_change", object_id=quote(obj.pk)) if obj is not None else self._reverse(f"{opts.app_label}_{opts.model_name}_changelist"),
            "management_siblings": sorted(self._management_buttons(request, page.scope, obj), key=lambda b: b["page"].group),
            "management_app_url": self._reverse("app_list", app_label=opts.app_label),
            "management_endpoint_names": {e.name: f"{self.admin_site.name}:{self.management_url_name(page, e)}" for e in page.endpoints},
            "has_permission": True,
        }

    def _management_view(self, page, endpoint=None):
        target = endpoint.view if endpoint else page.view
        methods = endpoint.methods if endpoint else ("GET", "HEAD")

        def dispatch(request, *args, **kwargs):
            obj = None
            if page.scope == "object":
                obj = self.get_object(request, unquote(kwargs.pop("object_id")))
                if obj is None:
                    raise Http404
            if not self._allowed(request, page, obj):
                raise PermissionDenied
            if endpoint and endpoint.permission and not request.user.has_perm(endpoint.permission):
                raise PermissionDenied
            if request.method not in methods:
                return HttpResponseNotAllowed(methods)
            request.current_app = self.admin_site.name
            context = self.management_context(request, page) if obj is None else self.management_context(request, page, obj)
            request.fdg_management_object = obj
            request.fdg_management_context = context
            if endpoint:
                response = target(request, *args, **kwargs)
                if page.audit:
                    logger.info("management endpoint", extra={"fdg_actor": str(request.user.pk), "fdg_model": self.model._meta.label, "fdg_object": str(obj.pk) if obj is not None else None, "fdg_page": page.name, "fdg_endpoint": endpoint.name, "fdg_method": request.method, "fdg_status": response.status_code})
                return response
            # Expose context to custom views before they run, including eager rendering.
            request.fdg_management_context = context
            if target is None:
                return TemplateResponse(request, page.template_name, context)
            response = target(request, *args, **kwargs)
            if isinstance(response, TemplateResponse) and not response.is_rendered:
                response.context_data = {**context, **(response.context_data or {})}
            return response

        # Do not copy csrf_exempt from arbitrary target views.
        secured = csrf_protect(dispatch)
        if not endpoint:
            secured = ensure_csrf_cookie(secured)
        return self.admin_site.admin_view(secured)

    def get_urls(self):
        custom = []
        for page in self.get_management_pages():
            if page.url_name:
                continue
            prefix = f"manage/{page.name}/" if page.scope == "model" else f"manage-object/<str:object_id>/{page.name}/"
            for endpoint in page.endpoints:
                custom.append(path(prefix + endpoint.route, self._management_view(page, endpoint), name=self.management_url_name(page, endpoint)))
            custom.append(path(prefix, self._management_view(page), name=self.management_url_name(page)))
        return custom + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        context = dict(extra_context or {})
        context["fdg_management_buttons"] = self._management_buttons(request, "model")
        context["fdg_management_changelist_base"] = self.management_changelist_base
        return super().changelist_view(request, extra_context=context)

    def _allowed(self, request, page, obj):
        # Preserve 0.1 overrides for model-level pages.
        return self.has_management_permission(request, page) if obj is None else self.has_management_permission(request, page, obj)

    def _management_buttons(self, request, scope, obj=None):
        return [{"page": p, "url": self.management_url(p, obj)}
                for p in self.get_management_pages()
                if p.scope == scope and self._allowed(request, p, obj)]

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["fdg_management_buttons"] = self._management_buttons(request, "object", obj) if obj is not None and not add else []
        context["fdg_management_changeform_base"] = self.management_changeform_base
        return super().render_change_form(request, context, add, change, form_url, obj)
