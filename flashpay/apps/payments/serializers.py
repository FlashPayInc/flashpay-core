from typing import Any

from django.db.models import Sum

from rest_framework.serializers import ModelSerializer, SerializerMethodField, ValidationError

from flashpay.apps.core.serializers import AssetSerializer
from flashpay.apps.payments.models import PaymentLink, PaymentLinkTransaction


class PaymentLinkSerializer(ModelSerializer):

    asset = AssetSerializer()

    class Meta:

        model = PaymentLink
        exclude = ("deleted_at", "account")


class PaymentLinkDetailSerializer(PaymentLinkSerializer):

    total_revenue = SerializerMethodField()

    def get_total_revenue(self, obj: PaymentLink) -> float:
        total = PaymentLinkTransaction.objects.filter(payment_link=obj).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        return float(total) if total else 0.0

    class Meta(PaymentLinkSerializer.Meta):
        pass


class CreatePaymentLinkSerializer(ModelSerializer):
    class Meta:
        model = PaymentLink
        fields = (
            "name",
            "image",
            "description",
            "asset",
            "amount",
            "has_fixed_amount",
            "is_one_time",
        )

    def validate(self, attrs: Any) -> Any:
        # check amount and fixed amount fields
        if (attrs["has_fixed_amount"] and attrs["amount"] <= 0) or attrs["amount"] < 0:
            raise ValidationError(detail="Invalid Amount")
        return super().validate(attrs)


class PaymentLinkTransactionSerializer(ModelSerializer):
    class Meta:
        model = PaymentLinkTransaction
        exclude = ("payment_link",)
