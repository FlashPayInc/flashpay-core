from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.account.utils import generate_api_key
from flashpay.apps.core.models import Network


@receiver(post_save, sender=Account)
def create_api_keys(instance: Account, **kwargs: Any) -> None:
    if instance.is_verified and instance.api_keys.count() != 2:
        test_secret, test_public = generate_api_key(instance.address, Network.TESTNET)
        main_secret, main_public = generate_api_key(instance.address, Network.MAINNET)
        APIKey.objects.create(
            secret_key=test_secret,
            public_key=test_public,
            account=instance,
            network=Network.TESTNET,
        )
        APIKey.objects.create(
            secret_key=main_secret,
            public_key=main_public,
            account=instance,
            network=Network.MAINNET,
        )
