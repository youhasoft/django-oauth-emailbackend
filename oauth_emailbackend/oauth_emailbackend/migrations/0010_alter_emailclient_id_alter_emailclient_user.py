# Generated by Django 5.0.2 on 2024-03-06 09:38

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0009_alter_oauthapi_options_emailclient_delete_emailhost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailclient',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='emailclient',
            name='user',
            field=models.CharField(default='', max_length=70, verbose_name='사용자 이메일'),
        ),
    ]
