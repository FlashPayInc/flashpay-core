import pytest

from flashpay.apps.core.models import Asset


@pytest.mark.django_db
def test_create_asset() -> None:
    data = {
        "asa_id": 0,
        "short_name": "ALGO",
        "long_name": "ALGORAND",
        "image_url": "https://flashpay.com/img.png",
    }
    asset = Asset.objects.create(**data)

    assert asset.asa_id == data["asa_id"]
    assert asset.short_name == data["short_name"]
    assert asset.long_name == data["long_name"]
    assert asset.image_url == data["image_url"]
    assert str(asset) == asset.long_name
