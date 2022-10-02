# Generated by Django 3.2.15 on 2022-10-02 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='network',
            field=models.CharField(choices=[('mainnet', 'Mainnet'), ('testnet', 'Testnet')], default='mainnet', max_length=20),
        ),
    ]