from rest_framework import serializers
from .models import Device

class DeviceSerializer(serializers.ModelSerializer):
    last_toggled_by_name = serializers.ReadOnlyField(source='last_toggled_by.username', default='Система')

    class Meta:
        model = Device
        fields = ['id', 'name', 'device_type', 'is_active', 'last_toggled_by', 'last_toggled_by_name', 'last_toggled_at']
        read_only_fields = ['last_toggled_by', 'last_toggled_at']