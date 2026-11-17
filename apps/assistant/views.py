import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssistantConfiguration
from .serializers import AssistantChatSerializer
from .services import GeminiServiceError, ask_gemini, enforce_rate_limit

logger = logging.getLogger(__name__)

SUGGESTED_QUESTIONS = [
    'Как работает аквапоника?',
    'За что отвечает ESP32?',
    'Как система следит за качеством воды?',
    'Как компьютерное зрение анализирует растения?',
]


class AssistantConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        config = AssistantConfiguration.get_solo()
        return Response({
            'name': 'AQ Assistant',
            'welcome_message': config.welcome_message,
            'suggested_questions': SUGGESTED_QUESTIONS,
            'available': bool(settings.GEMINI_API_KEY),
        })


class AssistantChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AssistantChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        config = AssistantConfiguration.get_solo()
        client_address = request.META.get('REMOTE_ADDR', 'unknown')
        address_hash = hashlib.sha256(client_address.encode('utf-8')).hexdigest()
        if not enforce_rate_limit(address_hash, config.requests_per_minute):
            return Response(
                {'error': 'Слишком много запросов. Попробуйте через минуту.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={'Retry-After': '60'},
            )

        try:
            reply = ask_gemini(
                message=serializer.validated_data['message'],
                history=serializer.validated_data['history'],
                model_name=config.model_name or settings.GEMINI_MODEL,
            )
        except GeminiServiceError as error:
            logger.info('AQ Assistant is unavailable: %s', error)
            return Response(
                {'error': 'AI-консультант временно недоступен. Попробуйте позже.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({'reply': reply})
