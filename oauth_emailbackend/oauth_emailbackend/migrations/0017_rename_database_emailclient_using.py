# Generated by Django 5.0.2 on 2024-03-29 08:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0016_remove_emailclient_user_emailclient_api_email_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailclient',
            old_name='database',
            new_name='using',
        ),
    ]