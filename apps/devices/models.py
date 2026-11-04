from django.db import models
from django.conf import settings

class DeviceType(models.TextChoices):
    PUMP = 'PUMP', 'Водяная помпа'
    AERATOR = 'AERATOR', 'Аэратор (компрессор)'
    LIGHT = 'LIGHT', 'Фитолампа'

class Device(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название устройства")
    device_type = models.CharField(max_length=20, choices=DeviceType.choices, unique=True, verbose_name="Тип устройства")
    is_active = models.BooleanField(default=False, verbose_name="Состояние (ВКЛ/ВЫКЛ)")
    last_toggled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Кто переключил"
    )
    last_toggled_at = models.DateTimeField(auto_now=True, verbose_name="Время переключения")

    class Meta:
        verbose_name = "Устройство (Реле)"
        verbose_name_plural = "Устройства (Реле)"

    def __str__(self):
        return f"{self.name} - {'ВКЛ' if self.is_active else 'ВЫКЛ'}"