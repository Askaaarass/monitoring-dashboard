from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Пользователь"
    )
    action = models.CharField(max_length=255, verbose_name="Действие")
    details = models.TextField(blank=True, null=True, verbose_name="Детали")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время действия")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Журнал аудита"
        verbose_name_plural = "Журналы аудита"

    def __str__(self):
        user_str = self.user.username if self.user else "Система"
        return f"[{self.timestamp.strftime('%d.%m.%Y %H:%M:%S')}] {user_str}: {self.action}"