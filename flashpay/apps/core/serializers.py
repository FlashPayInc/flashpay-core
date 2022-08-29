from rest_framework.serializers import ModelSerializer

from flashpay.apps.core.models import Asset


class AssetSerializer(ModelSerializer):
    class Meta:
        model = Asset
        fields = (
            "asa_id",
            "short_name",
            "long_name",
            "image_url",
            "network",
            "decimals",
        )
