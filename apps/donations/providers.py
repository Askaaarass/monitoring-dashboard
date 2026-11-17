from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from django.conf import settings
from django.utils.module_loading import import_string


class PaymentProviderError(Exception):
    pass


class PaymentsDisabled(PaymentProviderError):
    pass


@dataclass(frozen=True)
class PaymentSession:
    provider_payment_id: str
    checkout_url: str


@dataclass(frozen=True)
class PaymentNotification:
    merchant_reference: str
    provider_payment_id: str
    status: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class PaymentStatus:
    provider_payment_id: str
    status: str
    amount: Decimal
    currency: str


class PaymentProvider(Protocol):
    name: str

    def createPayment(self, *, reference, amount, currency, donor_email, return_url, callback_url) -> PaymentSession:
        ...

    def getPaymentStatus(self, provider_payment_id) -> PaymentStatus:
        ...

    def verifyCallback(self, *, body: bytes, headers) -> PaymentNotification:
        ...

    def processRefund(self, provider_payment_id, amount: Decimal):
        ...


class DisabledPaymentProvider:
    name = 'disabled'

    def _raise_disabled(self):
        raise PaymentsDisabled(
            'Donations are disabled until the recipient and payment provider are approved.'
        )

    def createPayment(self, **kwargs):
        self._raise_disabled()

    def getPaymentStatus(self, provider_payment_id):
        self._raise_disabled()

    def verifyCallback(self, *, body, headers):
        self._raise_disabled()

    def processRefund(self, provider_payment_id, amount):
        self._raise_disabled()


def get_payment_provider():
    if not settings.DONATIONS_ENABLED:
        return DisabledPaymentProvider()
    provider_path = settings.PAYMENT_PROVIDER_CLASS
    if not provider_path:
        raise PaymentsDisabled('No approved payment provider is configured.')
    provider_class = import_string(provider_path)
    return provider_class()
