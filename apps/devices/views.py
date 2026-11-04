from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.analytics.models import AuditLog
from .models import Device
from .serializers import DeviceSerializer

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Переключить состояние реле (ВКЛ/ВЫКЛ) с записью в аудит"""
        device = self.get_object()
        device.is_active = not device.is_active
        device.last_toggled_by = request.user
        device.save()

        # Логируем действие пользователя
        status_str = "ВКЛЮЧЕНО" if device.is_active else "ВЫКЛЮЧЕНО"
        AuditLog.objects.create(
            user=request.user,
            action=f"Переключение устройства {device.name}",
            details=f"Новое состояние: {status_str}"
        )

        return Response({
            'status': 'success',
            'id': device.id,
            'is_active': device.is_active,
            'message': f'{device.name} {status_str}'
        })