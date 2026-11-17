from rest_framework import serializers


class ConversationTurnSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=('user', 'assistant'))
    content = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


class AssistantChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)
    history = ConversationTurnSerializer(many=True, required=False, default=list, max_length=12)

    def validate_history(self, history):
        return history[-12:]
