import copy
import base64
from email.message import Message
from email.mime.base import MIMEBase
import subprocess
from typing import Any, Optional, Type, TypeVar
import typing

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.conf import settings
from django.apps import apps
from functools import lru_cache
from django.utils.timezone import now
from django.core.mail import EmailMessage
from django.contrib.sites.models import Site
from django.db.models import Model

T = TypeVar('T', bound=Model)



OS_MTA = getattr( settings, "OAUTH_EMAILBACKEND_MTA", None)
ADMINS = getattr( settings, "ADMINS", [])

@lru_cache
def get_provider_choices():
    # 등록된 provider 목록 
    providers = []
    for provider_name, klass in apps.get_app_config('oauth_emailbackend').providers.items():
        providers.append((provider_name, klass.provider_name))

    return providers

@lru_cache
def get_provider_name(provider_name):
    klass = apps.get_app_config('oauth_emailbackend').providers.get(provider_name, None)
    if klass:
        return klass.provider_name

def get_provider_instance(provider_name):
    # 지정된 프로바이더 인스턴스 
    return apps.get_app_config('oauth_emailbackend').providers[provider_name]()
    
def get_use_celery():
    return apps.get_app_config('oauth_emailbackend').use_celery

def _strip_message_id(message_id):
    return message_id.strip()[1:-1]

def mark_send_history_by_instance(instance: Type[T], success: bool, error_message: typing.Optional[str]=None, retry_count: typing.Optional[int]=0) -> None:
    try:
        instance.mark(success, error_message, retry_count)
    except Exception as e:
        print(e)
        
def mark_send_history(message_id, success: bool, error_message: typing.Optional[str]=None, retry_count: typing.Optional[int]=0) -> None:
    """발송이력을 마크한다."""
    from .models import SendHistory 

    try:
        obj = SendHistory.objects.get(message_id=_strip_message_id(message_id))
        obj.mark(success, error_message, retry_count)
        
    except Exception as e:
        print(e)
        # Send error message using user's os system email
        # send_system_email(subject, body)

# python 3.9 compatibility
# def add_send_history(message_id, site: Site, message: Optional[EmailMessage | Message], using='default', success=None, **kwargs) -> Optional[ Type[T]]: 
def add_send_history(message_id, site: Site, message, using='default', success=None, **kwargs) -> Optional[ Type[T]]: 
    """ 발송히스토리를 생성한다. """
    from .models import SendHistory 
    try:
        message_id = _strip_message_id(message_id)

        obj, created = SendHistory.objects.using(using).get_or_create(
                    message_id=message_id,
                    site=site,
                )
        if success is not None:
            obj.success = success 
            obj.sent_time = now()

        if created:
            if isinstance(message, (EmailMessage,)):
                subject = message.subject or kwargs.get('subject')
                recipients = message.recipients() or kwargs.get('recipients')
                body = message.body or kwargs.get('body')
            else:
                subject = kwargs.get('subject')
                recipients = kwargs.get('recipients')
                body = str(message)


            if isinstance(subject, (list, tuple)):
                subject = subject[0]
            
            if isinstance(recipients, (list, tuple)):
                recipients = recipients[0]

                if isinstance(recipients, (list, tuple)):
                    recipients = recipients[0]

            obj.recipients = recipients
            obj.subject = subject
            obj.raw = body

        obj.save()
        return obj
    
    except Exception as e:
        print(e)

def update_message_id(old_id, new_id):
    from .models import SendHistory 

    try:
        obj = SendHistory.objects.get(message_id=_strip_message_id(old_id))
        print('#1', obj)
        obj.message_id = _strip_message_id(new_id)
        obj.save(update_fields=['message_id'])
        print('#2', obj)

        return True
    except Exception as e:
        print(e)
        return False
    
def send_system_email(subject, body):
    """시스템 이메일로 발송 """
    if OS_MTA and ADMINS:
        for to_name, to_address in ADMINS:
            cmd = f""" echo "{{body}}" | mail -s "{{subject}}" {to_address}"""
            sendmail = subprocess.Popen(cmd, shell=True)
            # sendmail.wait()

def chunked(iterator, chunksize):
    """
    Yields items from 'iterator' in chunks of size 'chunksize'.

    >>> list(chunked([1, 2, 3, 4, 5], chunksize=2))
    [(1, 2), (3, 4), (5,)]
    """
    chunk = []
    for idx, item in enumerate(iterator, 1):
        chunk.append(item)
        if idx % chunksize == 0:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def email_to_dict(message):
    if isinstance(message, dict):
        return message

    message_dict = {'subject': message.subject,
                    'body': message.body,
                    'from_email': message.from_email,
                    'to': message.to,
                    'bcc': message.bcc,
                    # ignore connection
                    'attachments': [],
                    'headers': message.extra_headers,
                    'cc': message.cc}

    # Django 1.8 support
    # https://docs.djangoproject.com/en/1.8/topics/email/#django.core.mail.EmailMessage
    if hasattr(message, 'reply_to'):
        message_dict['reply_to'] = message.reply_to

    if hasattr(message, 'alternatives'):
        message_dict['alternatives'] = message.alternatives
    if message.content_subtype != EmailMessage.content_subtype:
        message_dict["content_subtype"] = message.content_subtype
    if message.mixed_subtype != EmailMessage.mixed_subtype:
        message_dict["mixed_subtype"] = message.mixed_subtype

    attachments = message.attachments
    for attachment in attachments:
        if isinstance(attachment, MIMEBase):
            filename = attachment.get_filename('')
            binary_contents = attachment.get_payload(decode=True)
            mimetype = attachment.get_content_type()
        else:
            filename, binary_contents, mimetype = attachment
        contents = base64.b64encode(binary_contents).decode('ascii')
        message_dict['attachments'].append((filename, contents, mimetype))

    return message_dict


def dict_to_email(messagedict):
    messagedict = copy.deepcopy(messagedict)
    extra_attrs = {}
    attachments = messagedict.pop('attachments')
    messagedict['attachments'] = []
    for attachment in attachments:
        filename, contents, mimetype = attachment
        binary_contents = base64.b64decode(contents.encode('ascii'))
        messagedict['attachments'].append(
            (filename, binary_contents, mimetype))
    if isinstance(messagedict, dict) and "content_subtype" in messagedict:
        content_subtype = messagedict["content_subtype"]
        del messagedict["content_subtype"]
    else:
        content_subtype = None
    if isinstance(messagedict, dict) and "mixed_subtype" in messagedict:
        mixed_subtype = messagedict["mixed_subtype"]
        del messagedict["mixed_subtype"]
    else:
        mixed_subtype = None
    if hasattr(messagedict, 'from_email'):
        ret = messagedict
    elif 'alternatives' in messagedict:
        ret = EmailMultiAlternatives(**messagedict)
    else:
        ret = EmailMessage(**messagedict)
    for attr, val in extra_attrs.items():
        setattr(ret, attr, val)
    if content_subtype:
        ret.content_subtype = content_subtype
        messagedict["content_subtype"] = content_subtype  # bring back content subtype for 'retry'
    if mixed_subtype:
        ret.mixed_subtype = mixed_subtype
        messagedict["mixed_subtype"] = mixed_subtype  # bring back mixed subtype for 'retry'

    return ret


def truncate_middle(line, n):
    if len(line) <= n:
        # string is already short-enough
        return line
    # half of the size, minus the 3 .'s
    n_2 = int(int(n) / 2 - 3)
    # whatever's left
    n_1 = n - n_2 - 3
    return '{0}...{1}'.format(line[:n_1], line[-n_2:])
