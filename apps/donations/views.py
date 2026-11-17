import logging
from urllib.parse import urlsplit

from django.conf import settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Donation, DonationStatus
from .providers import PaymentProviderError, PaymentsDisabled
from .serializers import DonationCreateSerializer
from .services import (
    DonationError,
    apply_verified_callback,
    create_donation,
    donation_statistics,
)

logger = logging.getLogger(__name__)


class DonationCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DonationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not settings.DONATIONS_ENABLED:
            return Response(
                {'error': 'Приём пожертвований пока отключён: платёжные реквизиты ещё не подтверждены.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            public_site_url = _get_public_site_url()
            provider = _get_provider()
            donation = create_donation(
                provider=provider,
                data=serializer.validated_data,
                return_url=f'{public_site_url}{reverse("donation-result")}',
                callback_url=f'{public_site_url}{reverse("donation-callback")}',
            )
        except PaymentsDisabled as error:
            return Response({'error': str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except (PaymentProviderError, DonationError) as error:
            logger.warning('Could not create donation payment: %s', error)
            return Response(
                {'error': 'Не удалось создать платёж. Попробуйте позже.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            {'id': str(donation.pk), 'checkout_url': donation.payment_url, 'status': donation.payment_status},
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_exempt, name='dispatch')
class DonationCallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not settings.DONATIONS_ENABLED:
            return Response({'error': 'Payments are disabled.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            provider = _get_provider()
            notification = provider.verifyCallback(body=request.body, headers=request.headers)
            donation = apply_verified_callback(provider=provider, notification=notification)
        except PaymentsDisabled as error:
            return Response({'error': str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except (PaymentProviderError, DonationError) as error:
            logger.warning('Rejected donation callback: %s', error)
            return Response({'error': 'Invalid payment notification.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'ok': True, 'status': donation.payment_status})


class DonationStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, donation_id):
        donation = Donation.objects.filter(pk=donation_id).only('id', 'payment_status').first()
        if donation is None:
            return Response({'error': 'Donation not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'id': str(donation.pk), 'status': donation.payment_status})


class DonationStatisticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(donation_statistics())


class DonationResultView(TemplateView):
    template_name = 'donations/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        donation_id = self.request.GET.get('id')
        donation = Donation.objects.filter(pk=donation_id).only('payment_status').first() if donation_id else None
        messages = {
            DonationStatus.PAID: 'Спасибо за поддержку Smart Aquaponics System!',
            DonationStatus.FAILED: 'Платёж не завершён. Вы можете попробовать ещё раз позже.',
            DonationStatus.CANCELLED: 'Платёж отменён.',
            DonationStatus.REFUNDED: 'Платёж возвращён.',
            DonationStatus.PENDING: 'Платёж обрабатывается. Проверьте статус позже.',
        }
        payment_status = donation.payment_status if donation else 'UNKNOWN'
        context.update({
            'payment_status': payment_status,
            'payment_message': messages.get(payment_status, 'Статус платежа пока недоступен.'),
        })
        return context


def _get_provider():
    from .providers import get_payment_provider

    return get_payment_provider()


def _get_public_site_url():
    public_site_url = settings.PUBLIC_SITE_URL.rstrip('/')
    try:
        parsed_url = urlsplit(public_site_url)
        port = parsed_url.port
    except ValueError as error:
        raise PaymentsDisabled('A canonical HTTPS public site URL is required for payments.') from error
    if (
        parsed_url.scheme != 'https'
        or not parsed_url.netloc
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
        or port not in (None, 443)
        or parsed_url.path not in ('', '/')
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise PaymentsDisabled('A canonical HTTPS public site URL is required for payments.')
    return public_site_url
