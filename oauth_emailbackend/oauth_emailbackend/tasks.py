from django.conf import settings
from django.core.mail import EmailMessage, get_connection
# from django.utils.six import string_types

from django.contrib.sites.models import Site

# Make sure our AppConf is loaded properly.
# import library.asyncmailer.conf  # noqa
from .utils import dict_to_email, email_to_dict 
from .models import EmailServerOption

try:
    from celery import shared_task

    TASK_CONFIG = {'name':  'oauth_emailbackend_using_celery', 
                'ignore_result': True,
                'rate_limit':    '30/m', # 분당 발송 건수 --2초 delay... 차후 다시 확인할 것 worker 단위 적용. 프로세스(concurrenty) 갯수와는 상관없음 
                }
    # TASK_CONFIG = {'name': 'asyncmailer', 'ignore_result': True}
    TASK_CONFIG.update(settings.CELERY_EMAIL_TASK_CONFIG)

    # import base if string to allow a base celery task
    if 'base' in TASK_CONFIG and isinstance(TASK_CONFIG['base'], string_types):
        from django.utils.module_loading import import_string
        TASK_CONFIG['base'] = import_string(TASK_CONFIG['base'])

    @shared_task(**TASK_CONFIG) 
    def send_emails(messages, site_id, 
                    email_server_database='default',
                    backend_kwargs=None, **kwargs):
        # backward compat: handle **kwargs and missing backend_kwargs
        """
        # by odop 2019.8.24
        # 복수의 이메일서버 중에 선택하여 발송할 수 있도록 변경 
        """
        
        combined_kwargs = {}
        from_email = reply_to = settings.DEFAULT_FROM_EMAIL
        
        if isinstance(email_server_name, (list, tuple)):
            email_server_name = email_server_name[0]
        
        if isinstance(email_server_database, (list, tuple)):
            email_server_database = email_server_database[0]
        
        site = Site.objects.using(email_server_database).filter(id=site_id,).last()
        email_server = EmailServerOption.objects.using(email_server_database).filter(site=site, 
                                                                            name=email_server_name,).last()
        
        # print(site, email_server)
        
        es = email_server
        if email_server and email_server.is_active:
            combined_kwargs['host'] = es.host
            combined_kwargs['port'] = es.port
            combined_kwargs['username'] = es.user 
            combined_kwargs['password'] = es.password
            combined_kwargs['use_tls'] = es.use_tls
            combined_kwargs['use_ssl'] = es.use_ssl
            
            from_email = es.from_email or from_email 
            reply_to = es.reply_to or reply_to 
            # by odop 2020.3.9
            # cc, bcc 직접 사용 
            #use_bcc = es.use_bcc
        else:
            combined_kwargs['host'] = settings.EMAIL_HOST
            combined_kwargs['port'] = settings.EMAIL_PORT
            combined_kwargs['username'] = settings.EMAIL_HOST_USER
            combined_kwargs['password'] = settings.EMAIL_HOST_PASSWORD
            combined_kwargs['use_tls'] = settings.EMAIL_USE_TLS
            
        if not isinstance(reply_to, (list, tuple)):
            reply_to = [reply_to]
            
        
        if backend_kwargs is not None:
            combined_kwargs.update(backend_kwargs)
        combined_kwargs.update(kwargs)
        
        # backward compat: catch single object or dict
        if isinstance(messages, (EmailMessage, dict)):
            messages = [messages]

        # make sure they're all dicts
        messages = [email_to_dict(m) for m in messages]
        #print(type(messages[0]))
        
        # by odop 2018.9.21
        # 보내일 메일과 리던 메일을 DB값으로 셋팅 
        for idx in range(0, len(messages)):
            messages[idx]['from_email'] = from_email
            messages[idx]['reply_to'] = reply_to
            
            # by odop 2020.3.9
            # settings.BCC_EMAILS 이 Celery에서 유효하지 않음으로 EmailServer에 직접 셋팅 
            if hasattr(es, 'cc') and es.cc:
                messages[idx]['cc'] = es.cc.split(",")
            if hasattr(es, 'bcc') and es.bcc:
                messages[idx]['bcc'] = es.bcc.split(",")
                
            print("*MessageID: ", messages[idx])
            
            
        conn = get_connection(backend=settings.CELERY_EMAIL_BACKEND, **combined_kwargs)
        try:
            conn.open()
        except Exception:
            logger.exception("Cannot reach CELERY_EMAIL_BACKEND %s", settings.CELERY_EMAIL_BACKEND)

        messages_sent = 0

        for message in messages:
            try:
                sent = conn.send_messages([dict_to_email(message)])
                if sent is not None:
                    messages_sent += sent
                logger.debug("Successfully sent email message to %r.", message['to'])
            except Exception as e:
                # Not expecting any specific kind of exception here because it
                # could be any number of things, depending on the backend
                logger.warning("Failed to send email message to %r, retrying. (%r)",
                            message['to'], e)
                send_emails.retry([[message], combined_kwargs], exc=e, throw=False)

        conn.close()
        return messages_sent


    # backwards compatibility
    SendEmailTask = send_email =  send_emails


    try:
        from celery.utils.log import get_task_logger
        logger = get_task_logger(__name__)
    except ImportError:
        logger = send_emails.get_logger()

except ImportError:
    pass