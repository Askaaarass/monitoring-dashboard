from rest_framework import serializers
from .models import BiomassIndex, Sensor, SensorData, Alert


class BiomassIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiomassIndex
        fields = ['value']

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ['id', 'sensor', 'value', 'timestamp']

class AlertSerializer(serializers.ModelSerializer):
    sensor_name = serializers.ReadOnlyField(source='sensor.name')

    class Meta:
        model = Alert
        fields = ['id', 'sensor', 'sensor_name', 'sensor_data', 'message', 'severity', 'is_resolved', 'created_at']

class SensorSerializer(serializers.ModelSerializer):
    latest_value = serializers.SerializerMethodField()
    is_alert = serializers.SerializerMethodField()

    class Meta:
        model = Sensor
        fields = ['id', 'name', 'sensor_type', 'unit', 'min_threshold', 'max_threshold', 'is_active', 'is_auto', 'latest_value', 'is_alert']

    def get_latest_value(self, obj):
        latest = obj.data_history.first()
        return latest.value if latest else 0.0

    def get_is_alert(self, obj):
        latest = self.get_latest_value(obj)
        return latest < obj.min_threshold or latest > obj.max_threshold