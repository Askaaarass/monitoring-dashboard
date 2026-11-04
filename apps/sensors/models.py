from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class BiomassIndex(models.Model):
    value = models.PositiveSmallIntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Индекс биомассы (%)",
    )

    class Meta:
        verbose_name = "Индекс биомассы"
        verbose_name_plural = "Индекс биомассы"

    @classmethod
    def current(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def __str__(self):
        return f"Индекс биомассы: {self.value}%"

class SensorType(models.TextChoices):
    WATER_TEMP = 'water_temp', 'Температура воды (°C)'
    PH = 'ph', 'Уровень pH'
    AIR_HUMIDITY = 'air_humidity', 'Влажность воздуха (%)'
    WATER_LEVEL = 'water_level', 'Уровень воды (%)'
    AIR_TEMP = 'air_temp', 'Температура воздуха (°C)'

class Sensor(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название датчика")
    sensor_type = models.CharField(max_length=30, choices=SensorType.choices, unique=True, verbose_name="Тип датчика")
    unit = models.CharField(max_length=15, verbose_name="Единица измерения")
    min_threshold = models.FloatField(verbose_name="Минимальный порог")
    max_threshold = models.FloatField(verbose_name="Максимальный порог")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_auto = models.BooleanField(default=True, verbose_name="Автоматическая симуляция")  # НОВОЕ ПОЛЕ

    class Meta:
        verbose_name = "Датчик"
        verbose_name_plural = "Датчики"

    def __str__(self):
        return f"{self.name} ({self.get_sensor_type_display()})"

class SensorData(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='data_history', verbose_name="Датчик")
    value = models.FloatField(verbose_name="Значение")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Время замера")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Запись показаний"
        verbose_name_plural = "Записи показаний"

    def __str__(self):
        return f"{self.sensor.name}: {self.value} {self.sensor.unit} [{self.timestamp.strftime('%H:%M:%S')}]"

class AlertSeverity(models.TextChoices):
    INFO = 'INFO', 'Информационный'
    WARNING = 'WARNING', 'Предупреждение'
    CRITICAL = 'CRITICAL', 'Критический'

class Alert(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='alerts', verbose_name="Датчик")
    sensor_data = models.ForeignKey(SensorData, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Запись замера")
    message = models.CharField(max_length=255, verbose_name="Сообщение")
    severity = models.CharField(max_length=20, choices=AlertSeverity.choices, default=AlertSeverity.WARNING, verbose_name="Уровень важности")
    is_resolved = models.BooleanField(default=False, verbose_name="Решено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата/Время спада")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Алерт"
        verbose_name_plural = "Алерты"

    def __str__(self):
        return f"[{self.severity}] {self.sensor.name}: {self.message}"