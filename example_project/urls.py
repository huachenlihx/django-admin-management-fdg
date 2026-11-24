from django.contrib import admin
from django.urls import path
from demo.admin import ItemAdmin
from demo.models import Item
from demo.views import external

other_site = admin.AdminSite(name='operations')
other_site.register(Item, ItemAdmin)
urlpatterns = [
  path('admin/', admin.site.urls),
  path('operations/', other_site.urls),
  path('existing/', external, name='demo_external')
]
