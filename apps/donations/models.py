import uuid

from django.core.validators import MinValueValidator
from django.db import models


class DonationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Ожидает оплаты'
    PAID = 'PAID', 'Оплачено'
    FAILED = 'FAILED', 'Ошибка оплаты'
    CANCELLED = 'CANCELLED', 'Отменено'
    REFUNDED = 'REFUNDED', 'Возвращено'


class Donation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    payment_provider = models.CharField(max_length=80, default='disabled')
    provider_payment_id = models.CharField(max_length=160, blank=True)
    payment_url = models.URLField(max_length=1000, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='KZT')
    donor_name = models.CharField(max_length=120, blank=True)
    donor_email = models.EmailField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=12,
        choices=DonationStatus.choices,
        default=DonationStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Пожертвование'
        verbose_name_plural = 'Пожертвования'

    def __str__(self):
        return f'{self.amount} {self.currency} · {self.payment_status}'
