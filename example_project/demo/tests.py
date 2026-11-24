from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, Client
from django.urls import reverse
from django_admin_management_fdg import ManagementPage, ManagementEndpoint
from .admin import ItemAdmin
from .models import Item
from django.contrib import admin

class ManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('root', 'root@example.com', 'password')
        self.client.force_login(self.user)
        self.ma = admin.site._registry[Item]
        self.page = self.ma.management_pages[0]
        self.url = self.ma.management_url(self.page)

    def endpoint(self, name, **kwargs):
        e = next(e for e in self.page.endpoints if e.name == name)
        return reverse('admin:' + self.ma.management_url_name(self.page, e), kwargs=kwargs or None)

    def test_buttons_and_standard_add(self):
        response = self.client.get(reverse('admin:demo_item_changelist'))
        for label in ('Manage Items', 'Reports', 'Existing Page', 'Add item'):
            self.assertContains(response, label)

    def test_custom_page_and_navigation(self):
        response = self.client.get(self.url)
        self.assertContains(response, reverse('admin:index'))
        self.assertContains(response, reverse('admin:demo_item_changelist'))
        self.assertContains(response, self.endpoint('create'))

    def test_template_page(self):
        self.assertContains(self.client.get(self.ma.management_url(self.ma.management_pages[1])), 'project-level templates')

    def test_crud_and_job(self):
        self.assertEqual(self.client.post(self.endpoint('create'), {'title': 'Sample'}).status_code, 201)
        item = Item.objects.get()
        self.assertEqual(self.client.patch(self.endpoint('publish', pk=item.pk)).status_code, 200)
        item.refresh_from_db(); self.assertTrue(item.published)
        self.assertEqual(self.client.post(self.endpoint('run_job')).status_code, 200)
        self.assertEqual(self.client.delete(self.endpoint('delete', pk=item.pk)).status_code, 200)
        self.assertFalse(Item.objects.exists())

    def test_methods(self):
        self.assertEqual(self.client.get(self.endpoint('create')).status_code, 405)
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_anonymous(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_staff_permissions(self):
        staff = get_user_model().objects.create_user('staff', password='password', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(codename='view_item'))
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.endpoint('create'), {'title': 'Denied'}).status_code, 403)

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.endpoint('create'), {'title': 'No token'}).status_code, 403)
        client.get(self.url)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.endpoint('create'), {'title': 'With token'}, HTTP_X_CSRFTOKEN=token).status_code, 201)

    def test_custom_admin_site(self):
        from urls import other_site
        other = other_site._registry[Item]
        url = other.management_url(self.page)
        self.assertTrue(url.startswith('/operations/'))
        self.assertContains(self.client.get(url), '/operations/demo/item/')

    def test_external(self):
        self.assertEqual(self.client.get(reverse('demo_external')).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('demo_external')).status_code, 403)

    def test_invalid_config(self):
        with self.assertRaises(ValueError): ManagementPage(name='bad/name', label='Bad', template_name='a')
        with self.assertRaises(ValueError): ManagementPage(name='bad', label='Bad')
        with self.assertRaises(ValueError): ManagementPage(name='bad', label='Bad', template_name='a', color='red;')
        with self.assertRaises(ValueError): ManagementEndpoint('create/', 'create', lambda r: None, methods=('INVALID',))

    def test_object_page_and_navigation(self):
        item = Item.objects.create(title='Object example')
        page = self.ma.management_pages[3]
        parent = reverse('admin:demo_item_change', args=[item.pk])
        url = self.ma.management_url(page, item)
        self.assertContains(self.client.get(parent), url)
        response = self.client.get(url)
        self.assertContains(response, 'Object example')
        self.assertContains(response, parent)
        self.assertNotContains(self.client.get(reverse('admin:demo_item_add')), 'Preview Item')
        self.assertNotContains(self.client.get(reverse('admin:demo_item_changelist')), 'Item Details')

    def test_object_endpoint_audit_and_permission(self):
        item = Item.objects.create(title='Target')
        other = Item.objects.create(title='Untouched')
        page = self.ma.management_pages[3]
        endpoint = reverse('admin:' + self.ma.management_url_name(page, page.endpoints[0]), kwargs={'object_id': item.pk})
        with self.assertLogs('django_admin_management_fdg.audit', level='INFO') as logs:
            self.assertEqual(self.client.post(endpoint).status_code, 200)
        self.assertEqual(logs.records[0].fdg_object, str(item.pk))
        item.refresh_from_db(); other.refresh_from_db()
        self.assertTrue(item.published); self.assertFalse(other.published)
        staff = get_user_model().objects.create_user('reader', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='view_item'))
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.ma.management_url(page, item)).status_code, 200)
        self.assertEqual(self.client.post(endpoint).status_code, 403)
        item.delete()
        self.assertEqual(self.client.get(reverse('admin:' + self.ma.management_url_name(page), kwargs={'object_id': 999999})).status_code, 404)

    def test_confirmation_and_group_navigation(self):
        item = Item.objects.create(title='Preview')
        response = self.client.get(reverse('admin:demo_item_change', args=[item.pk]))
        self.assertContains(response, 'data-fdg-confirm="Open this item preview?"')
        self.assertContains(self.client.get(self.url), 'Operations')
        self.assertContains(self.client.get(self.url), 'Analytics')

    def test_invalid_scope(self):
        with self.assertRaises(ValueError):
            ManagementPage(name='invalid', label='Invalid', template_name='a', scope='unknown')
        with self.assertRaises(ValueError):
            ManagementPage(name='invalid', label='Invalid', url_name='demo_external', scope='object')
