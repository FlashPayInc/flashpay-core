# Generated by Django 3.2.13 on 2022-08-25 00:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentlink',
            name='network',
            field=models.CharField(choices=[('mainnet', 'Mainnet'), ('testnet', 'Testnet')], default='mainnet', max_length=20),
        ),
        migrations.AddField(
            model_name='transaction',
            name='network',
            field=models.CharField(choices=[('mainnet', 'Mainnet'), ('testnet', 'Testnet')], default='mainnet', max_length=20),
        ),
    ]