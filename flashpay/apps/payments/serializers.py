from typing import Any

from django.conf import settings
from django.db.models import Sum

from rest_framework.serializers import ModelSerializer, SerializerMethodField, ValidationError

from flashpay.apps.account.models import Account
from flashpay.apps.core.serializers import AssetSerializer
from flashpay.apps.payments.models import PaymentLink, PaymentLinkTransaction


class PaymentLinkSerializer(ModelSerializer):

    asset = AssetSerializer()
    image = SerializerMethodField()

    def get_image(self, obj: PaymentLink) -> Any:
        return obj.image.url if bool(obj.image) is None else settings.DEFAULT_PAYMENT_LINK_IMAGE

    class Meta:

        model = PaymentLink
        exclude = ("deleted_at", "account")


class PaymentLinkDetailSerializer(PaymentLinkSerializer):

    total_revenue = SerializerMethodField()

    def get_total_revenue(self, obj: PaymentLink) -> str:
        total = PaymentLinkTransaction.objects.filter(payment_link=obj).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        return str(total) if (total is not None) else "0.00"

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
        if attrs["amount"] <= 0:
            raise ValidationError(
                detail={"amount": "Amount cannot be less than or equal to zero."}
            )
        # Attach Account creating the payment link
        account = Account.objects.get(address=self.context["request"].user.id)
        attrs["account"] = account
        return super().validate(attrs)


class PaymentLinkTransactionSerializer(ModelSerializer):
    class Meta:
        model = PaymentLinkTransaction
        exclude = ("payment_link",)
