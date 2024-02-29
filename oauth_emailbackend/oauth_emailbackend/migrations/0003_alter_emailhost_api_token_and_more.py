# Generated by Django 5.0.2 on 2024-02-29 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0002_remove_emailhost_api_client_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailhost',
            name='api_token',
            field=models.TextField(blank=True, null=True, verbose_name='API TOKEN'),
        ),
        migrations.AlterField(
            model_name='emailhost',
            name='security_protocol',
            field=models.CharField(blank=True, choices=[('tls', 'TLS'), ('ssl', 'SSL')], max_length=15, null=True, verbose_name='보안 프로토콜'),
        ),
        migrations.AlterField(
            model_name='emailhost',
            name='send_method',
            field=models.CharField(choices=[('smtp', '사용자 지정 SMTP 서버'), ('gmail', 'Gmail')], default='smtp', max_length=15, verbose_name='발송 방법'),
        ),
        migrations.AlterModelTable(
            name='emailhost',
            table='oauthemailbackend_emailhost',
        ),
        migrations.AlterModelTable(
            name='sendhistory',
            table='oauthemailbackend_emailsendhistory',
        ),
    ]
