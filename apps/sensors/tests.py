import asyncio

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from .models import BiomassIndex, Sensor, SensorData, SensorType


class GuestSensorApiTests(APITestCase):
    def setUp(self):
        self.sensor = Sensor.objects.create(
            name='Температура воды',
            sensor_type=SensorType.WATER_TEMP,
            unit='°C',
            min_threshold=20,
            max_threshold=30,
        )

    def test_anonymous_user_can_read_sensor_list(self):
        response = self.client.get('/api/v1/sensors/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.sensor.name)

    def test_anonymous_user_cannot_change_sensor_mode(self):
        response = self.client.post(
            f'/api/v1/sensors/{self.sensor.pk}/toggle_auto/',
        )

        self.assertEqual(response.status_code, 403)
        self.sensor.refresh_from_db()
        self.assertTrue(self.sensor.is_auto)

    def test_sensor_api_uses_air_humidity_and_air_temperature_types(self):
        response = self.client.get('/api/v1/sensors/')

        sensor_types = {choice[0] for choice in SensorType.choices}
        self.assertIn('air_humidity', sensor_types)
        self.assertIn('air_temp', sensor_types)
        self.assertNotIn('oxygen', sensor_types)
        self.assertNotIn('nitrates', sensor_types)
        self.assertEqual(response.status_code, 200)


class EngineerSensorControlTests(APITestCase):
    def setUp(self):
        self.sensor = Sensor.objects.create(
            name='Температура воды',
            sensor_type=SensorType.WATER_TEMP,
            unit='°C',
            min_threshold=20,
            max_threshold=30,
        )
        self.engineer = get_user_model().objects.create_user(
            username='sensor-engineer',
            password='test-password',
            role='ENGINEER',
        )
        self.client.force_authenticate(user=self.engineer)

    def test_engineer_can_open_test_control_page(self):
        self.client.force_login(self.engineer)
        response = self.client.get('/test-control/')

        self.assertEqual(response.status_code, 200)

    def test_engineer_can_set_manual_sensor_value(self):
        response = self.client.post(
            f'/api/v1/sensors/{self.sensor.pk}/set_manual_value/',
            {'value': 25.5},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            SensorData.objects.get(sensor=self.sensor).value,
            25.5,
        )

    def test_engineer_can_toggle_sensor_auto_mode(self):
        response = self.client.post(
            f'/api/v1/sensors/{self.sensor.pk}/toggle_auto/',
        )

        self.assertEqual(response.status_code, 200)
        self.sensor.refresh_from_db()
        self.assertFalse(self.sensor.is_auto)

    def test_engineer_cannot_edit_sensor_configuration(self):
        response = self.client.patch(
            f'/api/v1/sensors/{self.sensor.pk}/',
            {'name': 'Измененное название'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.sensor.refresh_from_db()
        self.assertEqual(self.sensor.name, 'Температура воды')


class GuestSensorWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.sensor = Sensor.objects.create(
            name='Температура воды',
            sensor_type=SensorType.WATER_TEMP,
            unit='°C',
            min_threshold=20,
            max_threshold=30,
        )

    def test_guest_connection_does_not_generate_sensor_data(self):
        async_to_sync(self._connect_and_check_guest)()

    async def _connect_and_check_guest(self):
        from config.asgi import application

        communicator = WebsocketCommunicator(application, '/ws/sensors/')
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()
        await asyncio.sleep(3.1)
        await communicator.disconnect()

        data_count = await database_sync_to_async(SensorData.objects.count)()
        self.assertEqual(data_count, 0)


class BiomassIndexApiTests(APITestCase):
    def setUp(self):
        self.url = '/api/v1/biomass-index/'

    def test_guest_can_read_biomass_index(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['value'], 80)

    def test_guest_cannot_change_biomass_index(self):
        response = self.client.post(self.url, {'value': 45}, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(BiomassIndex.current().value, 80)

    def test_admin_can_change_biomass_index(self):
        admin = get_user_model().objects.create_user(
            username='biomass-admin',
            password='test-password',
            role='ADMIN',
        )
        self.client.force_authenticate(user=admin)

        response = self.client.post(self.url, {'value': 45}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['value'], 45)
        self.assertEqual(BiomassIndex.current().value, 45)

    def test_biomass_index_must_be_between_zero_and_one_hundred(self):
        admin = get_user_model().objects.create_user(
            username='biomass-admin',
            password='test-password',
            role='ADMIN',
        )
        self.client.force_authenticate(user=admin)

        response = self.client.post(self.url, {'value': 101}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(BiomassIndex.current().value, 80)
