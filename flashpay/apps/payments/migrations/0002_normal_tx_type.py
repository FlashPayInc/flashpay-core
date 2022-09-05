# Generated by Django 3.2.15 on 2022-09-05 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='txn_type',
            field=models.CharField(choices=[('payment_link', 'Payment Link'), ('normal', 'Normal')], default='payment_link', max_length=50),
        ),
    ]
