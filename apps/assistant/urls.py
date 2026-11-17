from django.urls import path

from .views import AssistantChatView, AssistantConfigView

urlpatterns = [
    path('config/', AssistantConfigView.as_view(), name='assistant-config'),
    path('chat/', AssistantChatView.as_view(), name='assistant-chat'),
]
