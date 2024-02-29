# Generated by Django 5.0.2 on 2024-02-29 09:01

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0005_alter_emailhost_provider_alter_emailhost_send_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='provider',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='provider',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]