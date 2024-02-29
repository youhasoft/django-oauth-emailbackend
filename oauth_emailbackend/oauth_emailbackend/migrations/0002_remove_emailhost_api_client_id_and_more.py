# Generated by Django 5.0.2 on 2024-02-27 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailhost',
            name='api_client_id',
        ),
        migrations.RemoveField(
            model_name='emailhost',
            name='api_client_secret',
        ),
        migrations.RemoveField(
            model_name='emailhost',
            name='api_refresh_token',
        ),
        migrations.AddField(
            model_name='emailhost',
            name='api_token',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='API TOKEN'),
        ),
    ]
