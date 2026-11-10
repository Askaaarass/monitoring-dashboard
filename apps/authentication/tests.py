from django.test import TestCase
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm


class RegistrationSecurityTests(TestCase):
    def test_public_registration_cannot_assign_admin_role(self):
        response = self.client.post('/auth/register/', {
            'username': 'registration-role-test',
            'password1': 'Safe-password-8492!',
            'password2': 'Safe-password-8492!',
            'role': 'ADMIN',
        })

        self.assertRedirects(response, '/dashboard/')
        user = get_user_model().objects.get(username='registration-role-test')
        self.assertEqual(user.role, 'ENGINEER')
        self.assertNotIn('role', CustomUserCreationForm().fields)


class PublicProjectTests(TestCase):
    def test_project_page_links_to_monitoring_and_engineer_login(self):
        with self.assertNumQueries(0):
            response = self.client.get('/')

        self.assertContains(response, 'Автономный мини-аквапонный комплекс')
        self.assertContains(response, 'data-aqua-story')
        self.assertContains(response, 'target-complex.webp')
        self.assertContains(response, 'href="/dashboard/"')
        self.assertContains(response, 'href="/auth/login/"')
        self.assertNotContains(response, 'new WebSocket')


class GuestDashboardTests(TestCase):
    def test_anonymous_user_can_open_read_only_dashboard(self):
        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['gallery_photos']), 6)
        photo_times = [photo['captured_at'] for photo in response.context['gallery_photos']]
        self.assertEqual(photo_times, sorted(photo_times, reverse=True))
        page = response.content.decode()
        self.assertLess(page.index('Показания датчиков в реальном времени'), page.index('Индекс биомассы'))
        self.assertLess(page.index('Индекс биомассы'), page.index('Состояние устройств'))
        self.assertContains(response, 'Гостевой просмотр')
        self.assertNotContains(response, 'data-aqua-story')
        self.assertContains(response, 'Открыть фотогалерею')
        self.assertContains(response, 'Демо-фото')
        self.assertContains(response, 'Войти')
        self.assertNotContains(response, 'Пульт тестов')
        self.assertNotContains(response, 'CSV Отчет')
        self.assertNotContains(response, 'onclick="toggleDevice')

    def test_engineer_login_redirects_to_dashboard_with_test_control_link(self):
        get_user_model().objects.create_user(username='story-engineer', password='test-password')

        response = self.client.post(
            '/auth/login/', {'username': 'story-engineer', 'password': 'test-password'}, follow=True
        )

        self.assertRedirects(response, '/dashboard/')
        self.assertContains(response, 'Пульт тестов')
        self.assertContains(response, 'href="/test-control/"')

    def test_login_page_offers_guest_dashboard(self):
        response = self.client.get('/auth/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Продолжить как гость')


class AdminAppearanceTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin-appearance-test',
            email='admin@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin_user)

    def test_admin_index_uses_aquaponics_branding_and_styles(self):
        response = self.client.get('/admin/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Аквапоника · управление системой')
        self.assertContains(response, 'admin/css/aquaponics_admin.css')
        self.assertContains(response, 'К мониторингу')
        self.assertContains(response, 'Управление аквапонной системой')
        self.assertContains(response, 'admin-theme-toggle')
        self.assertContains(response, 'admin-apps-grid')
        self.assertContains(response, 'Журнал последних действий')

    def test_sensor_admin_list_is_searchable_and_loads(self):
        response = self.client.get('/admin/sensors/sensor/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Мониторинг')
        self.assertContains(response, 'Фильтр')

    def test_sensor_edit_form_uses_admin_design(self):
        from apps.sensors.models import Sensor, SensorType

        sensor = Sensor.objects.create(
            name='Тестовая влажность',
            sensor_type=SensorType.AIR_HUMIDITY,
            unit='%',
            min_threshold=40,
            max_threshold=70,
        )
        response = self.client.get(f'/admin/sensors/sensor/{sensor.pk}/change/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aquaponics_admin.css')
        self.assertContains(response, 'Сохранить')
