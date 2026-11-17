from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase
from google.genai import types

from .knowledge import SYSTEM_INSTRUCTIONS, build_system_instruction
from .models import AssistantConfiguration
from .services import ask_gemini


class AssistantApiTests(APITestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_public_config_does_not_expose_api_key(self):
        with override_settings(GEMINI_API_KEY='private-test-key'):
            response = self.client.get('/api/assistant/config/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['available'])
        self.assertNotIn('private-test-key', str(response.data))
        self.assertEqual(response.data['name'], 'AQ Assistant')

    @override_settings(GEMINI_API_KEY='')
    def test_chat_reports_missing_gemini_configuration(self):
        response = self.client.post(
            '/api/assistant/chat/',
            {'message': 'Как работает система?', 'history': []},
            format='json',
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data['error'], 'AI-консультант временно недоступен. Попробуйте позже.')

    def test_chat_rejects_empty_and_overlong_messages(self):
        empty = self.client.post('/api/assistant/chat/', {'message': '   '}, format='json')
        too_long = self.client.post(
            '/api/assistant/chat/',
            {'message': 'x' * 2001},
            format='json',
        )

        self.assertEqual(empty.status_code, 400)
        self.assertEqual(too_long.status_code, 400)

    @override_settings(GEMINI_API_KEY='configured-test-key')
    @patch('apps.assistant.views.ask_gemini', return_value='Ответ на языке посетителя.')
    def test_chat_passes_supported_language_history_and_project_model(self, ask_gemini):
        AssistantConfiguration.objects.create(
            pk=1,
            model_name='gemini-test-model',
            requests_per_minute=10,
        )
        response = self.client.post(
            '/api/assistant/chat/',
            {
                'message': 'ESP32 qanday ishlaydi?',
                'history': [{'role': 'user', 'content': 'Сұрақ'}],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['reply'], 'Ответ на языке посетителя.')
        self.assertEqual(ask_gemini.call_args.kwargs['model_name'], 'gemini-test-model')
        self.assertEqual(ask_gemini.call_args.kwargs['history'][0]['content'], 'Сұрақ')

    @override_settings(GEMINI_API_KEY='configured-test-key')
    @patch('apps.assistant.views.ask_gemini', return_value='Ограниченный ответ.')
    def test_chat_rate_limit_is_applied(self, ask_gemini):
        AssistantConfiguration.objects.create(pk=1, requests_per_minute=1)
        first = self.client.post('/api/assistant/chat/', {'message': 'Первый'}, format='json')
        second = self.client.post('/api/assistant/chat/', {'message': 'Второй'}, format='json')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        ask_gemini.assert_called_once()

    def test_knowledge_base_distinguishes_demo_and_planned_features(self):
        instructions = build_system_instruction()

        self.assertIn(SYSTEM_INSTRUCTIONS, instructions)
        self.assertIn('simulated', instructions)
        self.assertIn('planned', instructions)
        self.assertIn('Decision Tree Classifier', instructions)


class AssistantKnowledgeAdminModelTests(TestCase):
    def test_admin_can_add_project_specific_knowledge(self):
        from .models import KnowledgeDocument

        document = KnowledgeDocument.objects.create(
            title='Water cycle',
            slug='water-cycle',
            content='The pump returns water through the loop.',
        )
        self.assertIn(document.content, build_system_instruction())


@override_settings(GEMINI_API_KEY='test-api-key', GEMINI_REQUEST_TIMEOUT_SECONDS=7)
class GeminiServiceTests(TestCase):
    @patch('apps.assistant.services.genai.Client')
    def test_interaction_uses_stable_api_and_non_persistent_context(self, client_class):
        interaction_client = client_class.return_value
        interaction_client.interactions.create.return_value.output_text = 'A project answer.'

        answer = ask_gemini(
            message='How does the system work?',
            history=[{'role': 'user', 'content': 'What is ESP32?'}],
            model_name='gemini-test-model',
        )

        self.assertEqual(answer, 'A project answer.')
        client_class.assert_called_once_with(
            api_key='test-api-key',
            http_options=types.HttpOptions(timeout=7000),
        )
        request = interaction_client.interactions.create.call_args.kwargs
        self.assertEqual(request['api_version'], 'v1')
        self.assertFalse(request['store'])
        self.assertIn('PROJECT KNOWLEDGE BASE', request['system_instruction'])
        self.assertIn('gemini-test-model', request['model'])
        interaction_client.close.assert_called_once()
