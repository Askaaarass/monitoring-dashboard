import json
import random
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import BiomassIndex, Sensor, SensorData, Alert, AlertSeverity
from apps.devices.models import Device

class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'dashboard_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        initial_data = await self.get_current_state()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': initial_data
        }))

        self.keep_running = True
        self.loop_task = asyncio.create_task(self.sensor_simulation_loop())

    async def disconnect(self, close_code):
        self.keep_running = False
        if hasattr(self, 'loop_task'):
            self.loop_task.cancel()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def sensor_simulation_loop(self):
        while self.keep_running:
            await asyncio.sleep(3)
            data = await self.generate_and_save_data()
            
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'sensor_update',
                    'data': data
                }
            )

    async def sensor_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update_data',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_current_state(self):
        sensors = Sensor.objects.all()
        devices = Device.objects.all()

        sensors_list = []
        for s in sensors:
            recent_logs = list(s.data_history.all()[:10])[::-1]
            val = recent_logs[-1].value if recent_logs and s.is_active else None
            sensors_list.append({
                'id': s.id,
                'name': s.name,
                'sensor_type': s.sensor_type,
                'unit': s.unit,
                'is_active': s.is_active,
                'is_auto': s.is_auto,
                'current_value': val if s.is_active else None,
                'min_threshold': s.min_threshold,
                'max_threshold': s.max_threshold,
                'is_alert': (val < s.min_threshold or val > s.max_threshold) if (val and s.is_active) else False,
                'timestamps': [log.timestamp.strftime('%H:%M:%S') for log in recent_logs] if s.is_active else [],
                'values': [log.value for log in recent_logs] if s.is_active else []
            })

        devices_list = [{
            'id': d.id,
            'name': d.name,
            'device_type': d.device_type,
            'is_active': d.is_active
        } for d in devices]

        return {
            'sensors': sensors_list,
            'devices': devices_list,
            'biomass_index': BiomassIndex.current().value,
        }

    @database_sync_to_async
    def generate_and_save_data(self):
        sensors = Sensor.objects.all()
        devices = Device.objects.all()
        updated_sensors = []
        new_alerts = []

        for sensor in sensors:
            recent_logs = list(sensor.data_history.all()[:10])[::-1]

            if not sensor.is_active:
                updated_sensors.append({
                    'id': sensor.id,
                    'name': sensor.name,
                    'unit': sensor.unit,
                    'is_active': False,
                    'is_auto': sensor.is_auto,
                    'current_value': None,
                    'min_threshold': sensor.min_threshold,
                    'max_threshold': sensor.max_threshold,
                    'is_alert': False,
                    'timestamps': [],
                    'values': []
                })
                continue

            last_data = sensor.data_history.first()
            current_val = last_data.value if last_data else (sensor.min_threshold + sensor.max_threshold) / 2

            if current_val > 150 or current_val < 0:
                current_val = round((sensor.min_threshold + sensor.max_threshold) / 2, 2)

            # --- ЕСЛИ АВТО-РЕЖИМ ВКЛЮЧЕН — ГЕНЕРИРУЕМ НОВЫЕ РАНДОМНЫЕ ДАННЫЕ ---
            if sensor.is_auto:
                delta = round(random.uniform(-0.3, 0.3), 2)
                new_val = round(max(0, current_val + delta), 2)

                if random.random() < 0.03:
                    new_val = round(sensor.max_threshold + random.uniform(0.5, 1.5), 2)

                SensorData.objects.create(sensor=sensor, value=new_val)

                was_alert = (current_val < sensor.min_threshold or current_val > sensor.max_threshold)
                is_alert = new_val < sensor.min_threshold or new_val > sensor.max_threshold

                if is_alert and not was_alert:
                    alert_msg = f"Выход за границы порогов: {new_val} {sensor.unit}"
                    alert_obj = Alert.objects.create(
                        sensor=sensor,
                        message=alert_msg,
                        severity=AlertSeverity.WARNING
                    )
                    new_alerts.append({
                        'sensor_name': sensor.name,
                        'message': alert_msg,
                        'created_at': alert_obj.created_at.strftime('%H:%M:%S')
                    })
            else:
                # --- ЕСЛИ АВТО-РЕЖИМ ВЫКЛЮЧЕН — ИСПОЛЬЗУЕМ ЗНАЧЕНИЕ С ПОЛЗУНКА ---
                new_val = current_val
                is_alert = new_val < sensor.min_threshold or new_val > sensor.max_threshold

            recent_logs = list(sensor.data_history.all()[:10])[::-1]

            updated_sensors.append({
                'id': sensor.id,
                'name': sensor.name,
                'unit': sensor.unit,
                'is_active': True,
                'is_auto': sensor.is_auto,
                'current_value': new_val,
                'min_threshold': sensor.min_threshold,
                'max_threshold': sensor.max_threshold,
                'is_alert': is_alert,
                'timestamps': [log.timestamp.strftime('%H:%M:%S') for log in recent_logs],
                'values': [log.value for log in recent_logs]
            })

        devices_list = [{
            'id': d.id,
            'name': d.name,
            'device_type': d.device_type,
            'is_active': d.is_active
        } for d in devices]

        return {
            'sensors': updated_sensors,
            'devices': devices_list,
            'alerts': new_alerts,
            'biomass_index': BiomassIndex.current().value,
        }