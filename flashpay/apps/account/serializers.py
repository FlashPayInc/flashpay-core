import binascii
from typing import Any, Dict

from algosdk.encoding import is_valid_address
from cryptography.fernet import InvalidToken
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenRefreshSerializer

from rest_framework import serializers

from flashpay.apps.account.models import APIKey, Webhook
from flashpay.apps.account.tokens import CustomRefreshToken  # type: ignore[attr-defined]
from flashpay.apps.account.utils import generate_api_key
from flashpay.apps.core.models import Network
from flashpay.apps.core.utils import decrypt_fernet_message


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ("secret_key", "public_key", "network")


class CreateAPIKeySerializer(APIKeySerializer):
    class Meta(APIKeySerializer.Meta):
        read_only_fields = ("secret_key", "public_key")

    def validate(self, attrs: Any) -> Any:
        network = self.context["request"].network
        account = self.context["request"].user
        # If API Key exists, the system deletes the keys
        try:
            APIKey.objects.get(account=account, network=network).delete()
        except APIKey.DoesNotExist:
            pass
        secret_key, public_key = generate_api_key(account.address, network)
        attrs["account"] = account
        attrs["secret_key"] = secret_key
        attrs["public_key"] = public_key
        attrs["network"] = network
        return super().validate(attrs)


class BaseAccountSerializer(serializers.Serializer):
    payload = serializers.CharField(required=True)


class AccountWalletAuthenticationSerializer(BaseAccountSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Any:
        payload = attrs["payload"]
        try:
            decrypted_payload = decrypt_fernet_message(payload)
            # we don't need the nonce provided here.
            _, address = decrypted_payload.split(",")
        except (ValueError, InvalidToken, binascii.Error):
            raise serializers.ValidationError({"payload": "Invalid payload format provided"})

        # now validate the address
        cleaned_address = address.strip()
        if is_valid_address(cleaned_address) is False:
            raise serializers.ValidationError("Invalid algorand address provided.")

        return {"address": cleaned_address}


class AccountSetUpSerializer(BaseAccountSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Any:
        payload = attrs["payload"]
        try:
            decrypted_payload = decrypt_fernet_message(payload)
            nonce, address, txid = decrypted_payload.split(",")
        except (ValueError, InvalidToken, binascii.Error):
            raise serializers.ValidationError({"payload": "Invalid payload format provided"})

        # now validate the address
        cleaned_address = address.strip()
        if is_valid_address(cleaned_address) is False:
            raise serializers.ValidationError("Invalid algorand address provided.")

        return {
            "address": cleaned_address,
            "nonce": nonce.strip(),
            "txid": txid.strip(),
        }


class AccountNetworkUpdateSerializer(serializers.Serializer):
    network = serializers.ChoiceField(required=True, choices=Network.choices)


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ("url", "network")


class CreateWebhookSerializer(WebhookSerializer):
    class Meta(WebhookSerializer.Meta):
        read_only_fields = ("network",)

    def validate(self, attrs: Any) -> Any:
        network = self.context["request"].network
        account = self.context["request"].user
        # If webhook exists, delete existing webhook
        try:
            Webhook.objects.get(account=account, network=network).delete()
        except Webhook.DoesNotExist:
            pass

        attrs["account"] = account
        attrs["network"] = network
        return super().validate(attrs)


class CustomTokenRefreshSerializer(TokenRefreshSerializer):  # type: ignore[no-any-unimported]  # noqa: E501
    token_class = CustomRefreshToken


class CustomTokenBlacklistSerializer(TokenBlacklistSerializer):  # type: ignore[no-any-unimported]  # noqa: E501
    token_class = CustomRefreshToken
