from decimal import Decimal

from rest_framework import serializers


class DonationCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    donor_name = serializers.CharField(max_length=120, required=False, allow_blank=True, trim_whitespace=True)
    donor_email = serializers.EmailField(required=False, allow_blank=True)
    is_anonymous = serializers.BooleanField(required=False, default=False)
    idempotency_key = serializers.UUIDField()

    def validate(self, attrs):
        forbidden_fields = {'card_number', 'card_pan', 'cvv', 'cvc', 'expiry'}
        if forbidden_fields.intersection(self.initial_data):
            raise serializers.ValidationError(
                'Card data must be entered only on the payment provider hosted checkout.'
            )
        return attrs
