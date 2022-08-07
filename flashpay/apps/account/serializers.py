from typing import Any, Dict

from algosdk.encoding import is_valid_address

from rest_framework import serializers

from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.account.utils import generate_api_key
from flashpay.apps.core.utils import decrypt_fernet_message


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ("secret_key", "public_key", "network")


class CreateAPIKeySerializer(APIKeySerializer):
    class Meta(APIKeySerializer.Meta):
        read_only_fields = ("secret_key", "public_key")

    def validate(self, attrs: Any) -> Any:
        address = self.context["request"].user.id
        network = attrs.get("network", "mainnet")
        account = Account.objects.filter(address=address)
        if not account.exists():
            raise serializers.ValidationError(detail="Account not found")
        # If API Key exists, the system deletes the keys
        api_key = APIKey.objects.filter(account__address=address, network=network)
        if api_key.exists():
            api_key.delete()
        secret_key, public_key = generate_api_key(address, network)
        attrs["account"] = account.first()
        attrs["secret_key"] = secret_key
        attrs["public_key"] = public_key
        return super().validate(attrs)


class BaseAccountSerializer(serializers.Serializer):
    payload = serializers.CharField(required=True)


class AccountWalletAuthenticationSerializer(BaseAccountSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Any:
        payload = attrs["payload"]
        decrypted_payload = decrypt_fernet_message(payload)
        try:
            # we don't need the nonce provided here.
            _, address = decrypted_payload.split(",")
        except ValueError:
            raise serializers.ValidationError("Invalid payload format provided.")

        # now validate the address
        cleaned_address = address.strip()
        if is_valid_address(cleaned_address) is False:
            raise serializers.ValidationError("Invalid algorand address provided.")

        return {"address": cleaned_address}


class AccountSetUpSerializer(BaseAccountSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Any:
        payload = attrs["payload"]
        decrypted_payload = decrypt_fernet_message(payload)
        try:
            nonce, address, txid = decrypted_payload.split(",")
        except ValueError:
            raise serializers.ValidationError("Invalid payload format provided.")

        # now validate the address
        if is_valid_address(address) is False:
            raise serializers.ValidationError("Invalid algorand address provided.")

        return {
            "address": address.strip(),
            "nonce": nonce.strip(),
            "txid": txid.strip(),
        }
