# Generated by Django 5.0.2 on 2024-04-04 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0020_remove_sendhistory_body_sendhistory_raw_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sendhistory',
            name='id',
        ),
        migrations.AlterField(
            model_name='sendhistory',
            name='message_id',
            field=models.CharField(editable=False, max_length=100, primary_key=True, serialize=False),
        ),
    ]
