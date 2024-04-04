# Generated by Django 5.0.2 on 2024-04-04 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0019_emailclient_sender_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sendhistory',
            name='body',
        ),
        migrations.AddField(
            model_name='sendhistory',
            name='raw',
            field=models.TextField(blank=True, null=True, verbose_name='메시지 원본'),
        ),
        migrations.AlterField(
            model_name='emailclient',
            name='token_expiry',
            field=models.DateTimeField(blank=True, help_text='갱신일 이전에 자동 갱신 시도합니다.', null=True, verbose_name='Token 유효기간'),
        ),
        migrations.AlterField(
            model_name='sendhistory',
            name='message_id',
            field=models.UUIDField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sendhistory',
            name='sent_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='발송 완료시간'),
        ),
        migrations.AlterField(
            model_name='sendhistory',
            name='subject',
            field=models.CharField(max_length=200, null=True, verbose_name='제목'),
        ),
    ]
