from django.db import models
from django.conf import settings


class AssistantConfiguration(models.Model):
    model_name = models.CharField(max_length=100, default='gemini-3.6-flash')
    welcome_message = models.TextField(
        default=(
            "Здравствуйте! Я AQ Assistant.\n\n"
            "Я расскажу о Smart Aquaponics System, датчиках, ESP32 и технологиях проекта. "
            "Чем могу помочь?"
        )
    )
    requests_per_minute = models.PositiveSmallIntegerField(default=10)

    class Meta:
        verbose_name = 'Настройки AQ Assistant'
        verbose_name_plural = 'Настройки AQ Assistant'

    def __str__(self):
        return 'Настройки AQ Assistant'

    @classmethod
    def get_solo(cls):
        return cls.objects.get_or_create(
            pk=1,
            defaults={'model_name': settings.GEMINI_MODEL},
        )[0]


class KnowledgeDocument(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=160, unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('title',)
        verbose_name = 'Дополнение базы знаний'
        verbose_name_plural = 'Дополнения базы знаний'

    def __str__(self):
        return self.title
