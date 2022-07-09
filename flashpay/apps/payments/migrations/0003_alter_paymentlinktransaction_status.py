# Generated by Django 3.2.13 on 2022-06-20 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_alter_paymentlink_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlinktransaction',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')], default='pending', max_length=50),
        ),
    ]
