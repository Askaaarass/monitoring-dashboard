from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username', default='Система')

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'username', 'action', 'details', 'timestamp']