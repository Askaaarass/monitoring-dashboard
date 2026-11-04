import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.sensors.models import SensorData
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

@login_required
def export_csv_view(request):
    """Экспорт последних 1000 записей замеров в CSV-файл"""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="aquaponics_sensors_report.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID Замера', 'Датчик', 'Значение', 'Единица', 'Дата и Время'])

    sensor_data = SensorData.objects.select_related('sensor').all()[:1000]
    for log in sensor_data:
        writer.writerow([
            log.id,
            log.sensor.name,
            log.value,
            log.sensor.unit,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response