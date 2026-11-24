from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from .models import Item


def manage(request):
    return TemplateResponse(request, 'demo/manage.html', {'items': Item.objects.all().order_by('-created_at')})


def create(request):
    title = request.POST.get('title', '').strip()
    if not title or len(title) > 150:
        return JsonResponse({'error': 'Title must contain 1–150 characters'}, status=400)
    item = Item.objects.create(title=title)
    return JsonResponse({'id': item.pk}, status=201)


def publish(request, pk):
    item = get_object_or_404(Item, pk=pk)
    item.published = True
    item.save(update_fields=['published'])
    return JsonResponse({'published': True})


def delete(request, pk):
    get_object_or_404(Item, pk=pk).delete()
    return JsonResponse({'deleted': True})


def run_job(request):
    count = Item.objects.filter(published=False).update(published=True)
    return JsonResponse({'published_count': count})


def external(request):
    if not (
        request.user.is_active
        and request.user.is_staff
        and request.user.has_perm("demo.view_item")
    ):
        raise PermissionDenied

    request.current_app = admin.site.name

    context = {
        **admin.site.each_context(request),
        "title": "Existing protected page",
    }

    return TemplateResponse(
        request,
        "demo/external.html",
        context,
    )

def publish_object(request):
    item = request.fdg_management_object
    item.published = True
    item.save(update_fields=['published'])
    return JsonResponse({'published': True})

