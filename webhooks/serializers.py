from rest_framework import serializers
from .models import Organization, Payment

class WebhookSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payer_inn = serializers.CharField(max_length=12)
    document_number = serializers.CharField(max_length=50)
    document_date = serializers.DateTimeField()

    def create(self, validated_data):
        return Payment.objects.create(**validated_data)


class OrganizationBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['inn', 'balance']