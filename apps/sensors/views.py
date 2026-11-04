from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.authentication.permissions import IsAdminOrReadOnly
from .models import BiomassIndex, Sensor, SensorData, Alert, AlertSeverity
from .serializers import BiomassIndexSerializer, SensorSerializer, SensorDataSerializer, AlertSerializer

@login_required
def test_control_view(request):
    sensors = Sensor.objects.all()
    return render(request, 'test_control.html', {
        'sensors': sensors,
        'biomass_index': BiomassIndex.current().value,
    })


class BiomassIndexView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        return Response(BiomassIndexSerializer(BiomassIndex.current()).data)

    def post(self, request):
        serializer = BiomassIndexSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        biomass_index = BiomassIndex.current()
        biomass_index.value = serializer.validated_data['value']
        biomass_index.save(update_fields=['value'])
        return Response(BiomassIndexSerializer(biomass_index).data)

class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=['post'])
    def toggle_auto(self, request, pk=None):
        """Переключение между Авто и Ручным режимом"""
        sensor = self.get_object()
        sensor.is_auto = not sensor.is_auto
        sensor.save()
        return Response({'status': 'success', 'is_auto': sensor.is_auto})

    @action(detail=True, methods=['post'])
    def set_manual_value(self, request, pk=None):
        """Ручная установка значения с ползунка"""
        sensor = self.get_object()
        try:
            val = round(float(request.data.get('value', 0)), 2)
        except (ValueError, TypeError):
            return Response({'error': 'Некорректное значение'}, status=status.HTTP_400_BAD_REQUEST)

        # Автоматически отключаем Авто-режим, когда юзер двигает ползунок
        sensor.is_auto = False
        sensor.save()

        # Записываем замер
        data_obj = SensorData.objects.create(sensor=sensor, value=val)

        is_alert = val < sensor.min_threshold or val > sensor.max_threshold
        if is_alert:
            alert_msg = f"[ТЕСТ] Ручной ввод: {val} {sensor.unit} (Выход за норму)"
            Alert.objects.create(
                sensor=sensor,
                sensor_data=data_obj,
                message=alert_msg,
                severity=AlertSeverity.WARNING
            )

        return Response({
            'status': 'success',
            'sensor': sensor.name,
            'value': val,
            'is_auto': sensor.is_auto,
            'is_alert': is_alert
        })

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        sensor = self.get_object()
        limit = int(request.query_params.get('limit', 30))
        history_data = sensor.data_history.all()[:limit]
        serializer = SensorDataSerializer(history_data, many=True)
        return Response(serializer.data)

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = True
        alert.save()
        return Response({'status': 'alert resolved'})