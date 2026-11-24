from django.contrib import admin
from django_admin_management_fdg import ManagementAdminMixin, ManagementPage, ManagementEndpoint
from .models import Item
from . import views

@admin.register(Item)
class ItemAdmin(ManagementAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'published', 'created_at')
    search_fields = ('title',)
    list_filter = ('published',)
    management_pages = (
        ManagementPage(name='manage_items', label='Manage Items', icon='📋', group='Operations', audit=True, view=views.manage, permission='demo.view_item', endpoints=(
            ManagementEndpoint('create/', 'create', views.create, permission='demo.add_item'),
            ManagementEndpoint('publish/<int:pk>/', 'publish', views.publish, methods=('PATCH',), permission='demo.change_item'),
            ManagementEndpoint('delete/<int:pk>/', 'delete', views.delete, methods=('DELETE',), permission='demo.delete_item'),
            ManagementEndpoint('run-job/', 'run_job', views.run_job, permission='demo.change_item'),
        )),
        ManagementPage(name='reports', label='Reports', icon='📊', template_name='demo/reports.html', permission='demo.view_item', color='#417690', group='Analytics', order=10),
        ManagementPage(name='external', label='Existing Page', url_name='demo_external', permission='demo.view_item', order=20),
        ManagementPage(name='item_details', label='Item Details', scope='object', group='Item', template_name='demo/item_details.html', permission='demo.view_item', audit=True, endpoints=(
            ManagementEndpoint('publish/', 'publish', views.publish_object, permission='demo.change_item'),
        )),
        ManagementPage(name='item_preview', label='Preview Item', scope='object', group='Item', confirmation='Open this item preview?', template_name='demo/item_details.html', permission='demo.view_item'),
    )
