# Generated by Django 5.0.2 on 2024-03-28 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_emailbackend', '0010_alter_emailclient_id_alter_emailclient_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailclient',
            name='api_token',
        ),
        migrations.RemoveField(
            model_name='oauthapi',
            name='client_id',
        ),
        migrations.RemoveField(
            model_name='oauthapi',
            name='client_secret',
        ),
        migrations.AddField(
            model_name='emailclient',
            name='access_token',
            field=models.TextField(blank=True, null=True, verbose_name='접속 Token'),
        ),
        migrations.AddField(
            model_name='emailclient',
            name='next_token_refresh_date',
            field=models.DateField(blank=True, null=True, verbose_name='다음 Token 갱신일'),
        ),
        migrations.AddField(
            model_name='emailclient',
            name='refresh_token',
            field=models.TextField(blank=True, null=True, verbose_name='갱신 Token'),
        ),
        migrations.AddField(
            model_name='oauthapi',
            name='secret_file',
            field=models.JSONField(help_text='CLIENT_ID, CLIENT_SECRET이 포함된 보안 비밀번호 json 파일', null=True, verbose_name='클라이언트 보안 비밀번호'),
        ),
        migrations.AlterField(
            model_name='emailclient',
            name='database',
            field=models.CharField(default='default', help_text='이메일 발송 히스토리를 저장할 때 접속할 데이터베이스 이름입니다.', max_length=30, verbose_name='데이터베이스 이름'),
        ),
    ]