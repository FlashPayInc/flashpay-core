from typing import Any

from algosdk.encoding import is_valid_address

from rest_framework.serializers import ValidationError


class IsValidAlgorandAddress:
    def __init__(self, fields: list):
        self.fields = fields

    def __call__(self, attrs: dict) -> Any:
        for field, value in attrs.items():
            if field in self.fields:
                if not is_valid_address(value):
                    raise ValidationError({f"{field}": "Not a valid address"})
