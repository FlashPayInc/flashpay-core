from django.db import models

from flashpay.apps.core.models import BaseModel, timezone


class PaymentLink(BaseModel):

    asset = models.ForeignKey("core.Asset", on_delete=models.DO_NOTHING)
    account = models.ForeignKey("account.Account", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    is_active = models.BooleanField(default=True)
    has_fixed_amount = models.BooleanField()
    is_one_time = models.BooleanField()

    def __str__(self) -> str:
        return self.name


class BaseTransaction(models.Model):

    txn_ref = models.CharField(max_length=10)
    asset = models.ForeignKey("core.Asset", on_delete=models.DO_NOTHING)
    sender = models.CharField(max_length=58)
    recipient = models.CharField(max_length=58)
    txn_hash = models.TextField()
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"Txn {self.txn_ref}"


class PaymentLinkTransaction(BaseTransaction):

    payment_link = models.ForeignKey(PaymentLink, on_delete=models.DO_NOTHING)
