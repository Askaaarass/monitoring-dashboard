from decimal import Decimal
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Donation, DonationStatus
from .providers import PaymentProviderError


class DonationError(Exception):
    pass


def validate_checkout_url(url):
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError) as error:
        raise DonationError('The payment provider returned an invalid checkout URL.') from error
    allowed_hosts = {
        host.strip().lower()
        for host in getattr(settings, 'PAYMENT_CHECKOUT_ALLOWED_HOSTS', [])
        if host.strip()
    }
    if (
        parsed.scheme != 'https'
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or port not in (None, 443)
        or parsed.hostname.lower() not in allowed_hosts
    ):
        raise DonationError('The payment provider returned an untrusted checkout URL.')
    return url


def create_donation(*, provider, data, return_url, callback_url):
    key = data['idempotency_key']
    donor_name = '' if data['is_anonymous'] else data.get('donor_name', '')
    donor_email = '' if data['is_anonymous'] else data.get('donor_email', '')
    try:
        with transaction.atomic():
            donation = Donation.objects.create(
                idempotency_key=key,
                payment_provider=provider.name,
                amount=data['amount'],
                currency='KZT',
                donor_name=donor_name,
                donor_email=donor_email,
                is_anonymous=data['is_anonymous'],
            )
    except IntegrityError:
        donation = Donation.objects.get(idempotency_key=key)
        same_request = (
            donation.amount == data['amount']
            and donation.is_anonymous == data['is_anonymous']
            and donation.donor_name == donor_name
            and donation.donor_email == donor_email
        )
        if not same_request:
            raise DonationError('This idempotency key was already used for a different donation.')
        if not donation.payment_url:
            raise DonationError('The existing donation does not have a checkout URL.')
        return donation

    try:
        return_url = f'{return_url}?{urlencode({"id": str(donation.pk)})}'
        payment = provider.createPayment(
            reference=str(donation.id),
            amount=donation.amount,
            currency=donation.currency,
            donor_email=donation.donor_email,
            return_url=return_url,
            callback_url=callback_url,
        )
        donation.payment_url = validate_checkout_url(payment.checkout_url)
        donation.provider_payment_id = payment.provider_payment_id
        donation.save(update_fields=('payment_url', 'provider_payment_id'))
    except (PaymentProviderError, DonationError):
        donation.payment_status = DonationStatus.FAILED
        donation.save(update_fields=('payment_status',))
        raise
    return donation


def apply_verified_callback(*, provider, notification):
    try:
        donation_id = UUID(notification.merchant_reference)
        donation = Donation.objects.get(
            pk=donation_id,
            payment_provider=provider.name,
        )
    except (ValueError, Donation.DoesNotExist) as error:
        raise DonationError('Unknown donation reference.') from error

    if (
        donation.provider_payment_id != notification.provider_payment_id
        or donation.amount != notification.amount
        or donation.currency != notification.currency
    ):
        raise DonationError('The payment notification does not match the donation.')

    verified = provider.getPaymentStatus(notification.provider_payment_id)
    if (
        verified.provider_payment_id != donation.provider_payment_id
        or verified.amount != donation.amount
        or verified.currency != donation.currency
    ):
        raise DonationError('The verified payment details do not match the donation.')

    status_map = {
        'PAID': DonationStatus.PAID,
        'FAILED': DonationStatus.FAILED,
        'CANCELLED': DonationStatus.CANCELLED,
        'REFUNDED': DonationStatus.REFUNDED,
        'PENDING': DonationStatus.PENDING,
    }
    final_status = status_map.get(verified.status.upper())
    if not final_status:
        raise DonationError('The payment provider returned an unsupported status.')

    with transaction.atomic():
        donation = Donation.objects.select_for_update().get(pk=donation_id)
        if donation.payment_status == DonationStatus.REFUNDED:
            return donation
        if donation.payment_status == DonationStatus.PAID and final_status != DonationStatus.REFUNDED:
            return donation
        donation.payment_status = final_status
        donation.paid_at = timezone.now() if final_status == DonationStatus.PAID else None
        donation.save(update_fields=('payment_status', 'paid_at'))
    return donation


def donation_statistics():
    from django.db.models import Count, Sum

    stats = Donation.objects.filter(payment_status=DonationStatus.PAID).aggregate(
        count=Count('id'),
        total=Sum('amount'),
    )
    return {
        'confirmed_donations': stats['count'] or 0,
        'total_amount': str(stats['total'] or Decimal('0.00')),
        'currency': 'KZT',
    }
