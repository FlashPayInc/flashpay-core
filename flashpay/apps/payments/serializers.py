from typing import Any
from uuid import UUID

from django.conf import settings

from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    UUIDField,
    ValidationError,
)

from flashpay.apps.core.serializers import AssetSerializer
from flashpay.apps.payments.models import DailyRevenue, PaymentLink, Transaction
from flashpay.apps.payments.utils import check_if_address_opted_in_asa, generate_txn_reference
from flashpay.apps.payments.validators import IsValidAlgorandAddress


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

        # check that the asset provided is for the network
        if attrs["asset"].network != self.context["request"].network:
            raise ValidationError(
                detail={"asset": "This asset is not available for the specified network."}
            )

        # Attach Account creating the payment link
        attrs["account"] = self.context["request"].user
        attrs["network"] = self.context["request"].network
        return super().validate(attrs)


class TransactionSerializer(ModelSerializer):
    payment_link = UUIDField(write_only=True, required=False)

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
            "network",
            "payment_link",
        )
        read_only_fields = (
            "txn_hash",
            "txn_reference",
            "created_at",
            "updated_at",
            "network",
            "status",
        )
        validators = [IsValidAlgorandAddress(fields=["recipient", "sender"])]

    def create(self, validated_data: Any) -> Any:
        payment_link_uid = validated_data.pop("payment_link", None)
        validated_data["txn_reference"] = generate_txn_reference(uid=payment_link_uid)
        validated_data["network"] = self.context["request"].network
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

    def validate(self, attrs: Any) -> Any:
        network = self.context["request"].network
        # check that the asset provided is for the network
        if attrs["asset"].network != network:
            raise ValidationError(
                detail={"asset": "This asset is not available for the specified network."}
            )

        if attrs["sender"] == attrs["recipient"]:
            raise ValidationError({"sender": "Sender's address cannot be the same as recipient"})

        if attrs["recipient"] != self.context["request"].user.address:
            raise ValidationError({"recipient": "Invalid recipient address"})

        if not check_if_address_opted_in_asa(
            address=attrs["recipient"], asset_id=attrs["asset"].asa_id, network=network
        ):
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
            if attrs["recipient"] != payment_link.account.address:  # type: ignore[union-attr]
                raise ValidationError({"recipient": "recipient does not have a payment link"})
            if attrs["asset"] != payment_link.asset:
                raise ValidationError(
                    {"asset": "payment link asset does not match specified asset"}
                )

        return super().validate(attrs)


class TransactionDetailSerializer(ModelSerializer):
    asset = AssetSerializer()

    class Meta:
        model = Transaction
        fields = (
            "txn_reference",
            "txn_type",
            "asset",
            "sender",
            "recipient",
            "txn_hash",
            "amount",
            "status",
            "created_at",
            "updated_at",
            "network",
        )


class PaymentLinkSerializer(ModelSerializer):
    creator = SerializerMethodField()
    asset = AssetSerializer()
    image_url = SerializerMethodField()
    transactions = TransactionSerializer(many=True)

    def get_image_url(self, obj: PaymentLink) -> str:
        return str(obj.image.url) if bool(obj.image) else str(settings.DEFAULT_PAYMENT_LINK_IMAGE)

    def get_creator(self, obj: PaymentLink) -> str:
        return obj.account.address  # type: ignore

    class Meta:
        model = PaymentLink
        fields = (
            "uid",
            "asset",
            "creator",
            "name",
            "description",
            "slug",
            "amount",
            "total_revenue",
            "image_url",
            "is_active",
            "has_fixed_amount",
            "is_one_time",
            "network",
            "created_at",
            "updated_at",
            "transactions",
        )


class VerifyTransactionSerializer(Serializer):
    txn_reference = CharField(max_length=42)


class DailyRevenueSerializer(ModelSerializer):
    class Meta:
        model = DailyRevenue
        fields = "__all__"
