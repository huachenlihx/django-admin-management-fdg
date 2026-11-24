from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def management_endpoint_url(context, name, **kwargs):
    if context.get("management_object_id") is not None:
        kwargs["object_id"] = context["management_object_id"]
    return reverse(context['management_endpoint_names'][name], kwargs=kwargs or None)
