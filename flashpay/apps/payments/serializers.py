from typing import Any
from uuid import UUID

from algosdk.encoding import is_valid_address

from django.conf import settings

from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    UUIDField,
    ValidationError,
)

from flashpay.apps.account.models import Account
from flashpay.apps.core.serializers import AssetSerializer
from flashpay.apps.payments.models import PaymentLink, Transaction
from flashpay.apps.payments.utils import check_if_address_opted_in_asa, generate_txn_reference
from flashpay.apps.payments.validators import IsValidAlgorandAddress


class PaymentLinkSerializer(ModelSerializer):
    asset = AssetSerializer()
    image_url = SerializerMethodField()

    def get_image_url(self, obj: PaymentLink) -> str:
        return str(obj.image.url) if bool(obj.image) else str(settings.DEFAULT_PAYMENT_LINK_IMAGE)

    class Meta:
        model = PaymentLink
        fields = (
            "asset",
            "name",
            "description",
            "slug",
            "amount",
            "image_url",
            "is_active",
            "has_fixed_amount",
            "is_one_time",
        )


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


class TransactionSerializer(ModelSerializer):
    payment_link = UUIDField(write_only=True)

    class Meta:
        model = Transaction
        fields = (
            "txn_reference",
            "asset",
            "sender",
            "txn_type",
            "recipient",
            "txn_hash",
            "amount",
            "status",
            "created_at",
            "updated_at",
            "payment_link",
        )
        read_only_fields = ("txn_hash", "txn_reference", "created_at", "updated_at", "status")
        validators = [IsValidAlgorandAddress(fields=["recipient", "sender"])]

    def create(self, validated_data: Any) -> Any:
        payment_link_uid = validated_data.pop("payment_link", None)
        validated_data["txn_reference"] = generate_txn_reference(uid=payment_link_uid)
        return super().create(validated_data)

    def validate_payment_link(self, value: UUID) -> Any:
        try:
            PaymentLink.objects.get(uid=value)
        except PaymentLink.DoesNotExist:
            raise ValidationError("Payment link does not exist")
        else:
            return value

    def validate_amount(self, value: Any) -> Any:
        if value <= 0:
            raise ValidationError("Amount cannot be lesser than 0")
        return value

    def validate_recipient(self, value: Any) -> Any:
        if not is_valid_address(value):
            raise ValidationError("Not a valid address")
        return value

    def validate_sender(self, value: Any) -> Any:
        if not is_valid_address(value):
            raise ValidationError("Not a valid address")
        return value

    def validate(self, attrs: Any) -> Any:
        if not check_if_address_opted_in_asa(attrs["recipient"], attrs["asset"].asa_id):
            raise ValidationError({"recipient": "recipient is not opted in to the asset."})

        if attrs["txn_type"] == "payment_link":
            uid = attrs.get("payment_link", None)
            # Payment_link field is required if transaction type is payment_link
            if not uid:
                raise ValidationError({"payment_link": "field is required"})
            try:
                payment_link = PaymentLink.objects.get(uid=uid)
            except PaymentLink.DoesNotExist:
                raise ValidationError("Invalid payment link provided")

            # Check if payment link has fixed amount and amount is same
            if payment_link.has_fixed_amount and attrs["amount"] != payment_link.amount:
                raise ValidationError({"amount": "payment link has fixed amount"})
            if attrs["recipient"] != payment_link.account.address:  # type: ignore
                raise ValidationError({"recipient": "recipient does not have a payment link"})

        return super().validate(attrs)


class VerifyTransactionSerializer(Serializer):
    txn_reference = CharField(max_length=42)
