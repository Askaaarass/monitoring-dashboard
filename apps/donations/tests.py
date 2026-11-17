from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from .models import Donation, DonationStatus
from .providers import PaymentNotification, PaymentProviderError, PaymentSession, PaymentStatus
from .services import DonationError, apply_verified_callback, create_donation, donation_statistics


class FakePaymentProvider:
    name = 'sandbox-test'

    def __init__(self, payment_status='PAID'):
        self.payment_status = payment_status
        self.created = 0
        self.notification = None
        self.payment_kwargs = None

    def createPayment(self, **kwargs):
        self.created += 1
        self.payment_kwargs = kwargs
        return PaymentSession('provider-123', 'https://checkout.test.example/pay/123')

    def getPaymentStatus(self, provider_payment_id):
        return PaymentStatus(provider_payment_id, self.payment_status, Decimal('3000.00'), 'KZT')

    def verifyCallback(self, *, body, headers):
        if self.notification is None:
            raise PaymentProviderError('Invalid test signature.')
        return self.notification

    def processRefund(self, provider_payment_id, amount):
        return None


@override_settings(DONATIONS_ENABLED=False)
class DonationDisabledApiTests(APITestCase):
    def test_create_payment_is_disabled_and_creates_no_record(self):
        response = self.client.post(
            '/api/donations/create/',
            {'amount': '3000', 'idempotency_key': str(uuid4())},
            format='json',
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(Donation.objects.count(), 0)

    def test_create_requires_positive_amount_and_idempotency_key(self):
        response = self.client.post('/api/donations/create/', {'amount': '0'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Donation.objects.count(), 0)

    def test_card_data_is_rejected(self):
        response = self.client.post(
            '/api/donations/create/',
            {
                'amount': '3000',
                'idempotency_key': str(uuid4()),
                'card_number': '4111111111111111',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Donation.objects.count(), 0)

    def test_public_statistics_count_paid_donations_only(self):
        Donation.objects.create(amount='3000.00', payment_status=DonationStatus.PAID)
        Donation.objects.create(amount='1000.00', payment_status=DonationStatus.PENDING)
        Donation.objects.create(amount='5000.00', payment_status=DonationStatus.FAILED)

        response = self.client.get('/api/donations/statistics/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['confirmed_donations'], 1)
        self.assertEqual(response.data['total_amount'], '3000')
        self.assertNotIn('donor_name', response.data)
        self.assertNotIn('supporters', response.data)

    def test_status_endpoint_does_not_return_donor_information(self):
        donation = Donation.objects.create(
            amount='3000.00',
            donor_name='Private Donor',
            donor_email='private@example.com',
            payment_status=DonationStatus.PENDING,
        )

        response = self.client.get(f'/api/donations/status/{donation.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], DonationStatus.PENDING)
        self.assertNotIn('private@example.com', str(response.data))

    def test_callback_stays_disabled(self):
        response = self.client.post('/api/donations/callback/', '{}', content_type='application/json')

        self.assertEqual(response.status_code, 503)


@override_settings(
    DONATIONS_ENABLED=True,
    PAYMENT_CHECKOUT_ALLOWED_HOSTS=['checkout.test.example'],
)
class DonationProviderTests(TestCase):
    def setUp(self):
        self.provider = FakePaymentProvider()
        self.data = {
            'amount': Decimal('3000.00'),
            'donor_name': 'Test Donor',
            'donor_email': 'test@example.com',
            'is_anonymous': False,
            'idempotency_key': uuid4(),
        }

    def create(self):
        return create_donation(
            provider=self.provider,
            data=self.data,
            return_url='https://example.test/api/donations/result/',
            callback_url='https://example.test/api/donations/callback/',
        )

    def test_checkout_is_hosted_and_idempotent(self):
        first = self.create()
        second = self.create()

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(self.provider.created, 1)
        self.assertEqual(first.payment_url, 'https://checkout.test.example/pay/123')

    def test_anonymous_donation_does_not_store_identity(self):
        self.data['is_anonymous'] = True
        donation = self.create()

        self.assertEqual(donation.donor_name, '')
        self.assertEqual(donation.donor_email, '')

    def test_untrusted_checkout_url_is_rejected(self):
        class BadCheckoutProvider(FakePaymentProvider):
            def createPayment(self, **kwargs):
                return PaymentSession('provider-123', 'https://evil.example/collect')

        with self.assertRaises(DonationError):
            create_donation(
                provider=BadCheckoutProvider(),
                data=self.data,
                return_url='https://example.test/result/',
                callback_url='https://example.test/callback/',
            )
        self.assertEqual(Donation.objects.get(idempotency_key=self.data['idempotency_key']).payment_status, DonationStatus.FAILED)

    def test_callback_verifies_provider_status_and_is_idempotent(self):
        donation = self.create()
        self.provider.notification = PaymentNotification(
            merchant_reference=str(donation.pk),
            provider_payment_id=donation.provider_payment_id,
            status='PAID',
            amount=donation.amount,
            currency=donation.currency,
        )

        first = apply_verified_callback(provider=self.provider, notification=self.provider.notification)
        first_paid_at = first.paid_at
        second = apply_verified_callback(provider=self.provider, notification=self.provider.notification)

        self.assertEqual(first.payment_status, DonationStatus.PAID)
        self.assertIsNotNone(first_paid_at)
        self.assertEqual(second.paid_at, first_paid_at)
        self.assertEqual(donation_statistics()['confirmed_donations'], 1)

    def test_callback_amount_mismatch_is_rejected(self):
        donation = self.create()
        notification = PaymentNotification(
            merchant_reference=str(donation.pk),
            provider_payment_id=donation.provider_payment_id,
            status='PAID',
            amount=Decimal('5000.00'),
            currency='KZT',
        )

        with self.assertRaisesMessage(DonationError, 'does not match'):
            apply_verified_callback(provider=self.provider, notification=notification)
        donation.refresh_from_db()
        self.assertEqual(donation.payment_status, DonationStatus.PENDING)

    def test_provider_callback_requires_signature_verification(self):
        with patch('apps.donations.views._get_provider', return_value=self.provider):
            response = self.client.post(
                '/api/donations/callback/',
                '{}',
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 400)


@override_settings(
    DONATIONS_ENABLED=True,
    PAYMENT_CHECKOUT_ALLOWED_HOSTS=['checkout.test.example'],
    PUBLIC_SITE_URL='https://aquaponics.example',
)
class DonationCanonicalUrlTests(APITestCase):
    @patch('apps.donations.views._get_provider')
    def test_return_and_callback_urls_use_configured_public_origin(self, get_provider):
        provider = FakePaymentProvider()
        get_provider.return_value = provider
        response = self.client.post(
            '/api/donations/create/',
            {'amount': '3000', 'idempotency_key': str(uuid4())},
            format='json',
            HTTP_HOST='attacker.example',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            provider.payment_kwargs['return_url'].split('?')[0],
            'https://aquaponics.example/api/donations/result/',
        )
        self.assertEqual(
            provider.payment_kwargs['callback_url'],
            'https://aquaponics.example/api/donations/callback/',
        )

    @override_settings(PUBLIC_SITE_URL='')
    @patch('apps.donations.views._get_provider')
    def test_payment_creation_requires_configured_canonical_origin(self, get_provider):
        response = self.client.post(
            '/api/donations/create/',
            {'amount': '3000', 'idempotency_key': str(uuid4())},
            format='json',
        )

        self.assertEqual(response.status_code, 503)
        get_provider.assert_not_called()
        self.assertEqual(Donation.objects.count(), 0)
