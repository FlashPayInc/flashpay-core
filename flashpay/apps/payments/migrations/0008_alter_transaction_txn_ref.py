# Generated by Django 3.2.13 on 2022-08-01 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_alter_transaction_txn_ref'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='txn_ref',
            field=models.CharField(max_length=42, unique=True),
        ),
    ]
