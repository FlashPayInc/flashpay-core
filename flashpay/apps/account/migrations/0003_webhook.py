# Generated by Django 3.2.15 on 2022-10-01 15:32

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_change_default_network_to_mainnet'),
    ]

    operations = [
        migrations.CreateModel(
            name='Webhook',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('network', models.CharField(choices=[('mainnet', 'Mainnet'), ('testnet', 'Testnet')], default='mainnet', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(null=True)),
                ('url', models.URLField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='account.account')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]