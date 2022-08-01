# Generated by Django 3.2.13 on 2022-07-28 11:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_paymentlink_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlink',
            name='has_fixed_amount',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='image',
            field=models.ImageField(null=True, upload_to='payment-links'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='is_one_time',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='paymentlinktransaction',
            name='payment_link',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transactions', to='payments.paymentlink'),
        ),
    ]