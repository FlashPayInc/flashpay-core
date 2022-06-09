import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class Asset(BaseModel):

    asa_id = models.IntegerField()
    short_name = models.CharField(max_length=20)
    long_name = models.CharField(max_length=100)
    image_url = models.TextField()

    def __str__(self) -> str:
        return self.long_name
