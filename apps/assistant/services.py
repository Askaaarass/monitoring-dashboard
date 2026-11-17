import json
import logging

from django.conf import settings
from django.core.cache import cache
from google import genai
from google.genai import errors, types
import httpx2

from .knowledge import build_system_instruction

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    pass


def enforce_rate_limit(client_address, limit):
    key = f'aq-assistant:{client_address}'
    if not cache.add(key, 1, timeout=60):
        try:
            count = cache.incr(key)
        except ValueError:
            cache.add(key, 1, timeout=60)
            count = 1
        if count > limit:
            return False
    return True


def ask_gemini(*, message, history, model_name):
    if not settings.GEMINI_API_KEY:
        raise GeminiServiceError('AI assistant is not configured.')

    conversation = {
        'conversation_history': history,
        'current_user_message': message,
    }
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            timeout=settings.GEMINI_REQUEST_TIMEOUT_SECONDS * 1000,
        ),
    )
    try:
        interaction = client.interactions.create(
            api_version='v1',
            model=model_name,
            input=json.dumps(conversation, ensure_ascii=False),
            system_instruction=build_system_instruction(),
            store=False,
        )
    except (errors.APIError, httpx2.RequestError, TimeoutError) as error:
        logger.warning('Gemini request failed: %s', error)
        raise GeminiServiceError('AI assistant is temporarily unavailable.') from error
    finally:
        client.close()

    reply = (interaction.output_text or '').strip()
    if not reply:
        logger.warning('Gemini returned an empty assistant response.')
        raise GeminiServiceError('AI assistant returned an empty response.')
    return reply
