from django.conf import settings
from six import string_types
from django.core.mail import EmailMessage, get_connection
from .utils import dict_to_email, email_to_dict 
from .models import EmailClient

try:
    from celery import shared_task

    TASK_CONFIG = getattr(settings, "CELERY_EMAIL_TASK_CONFIG", {})
    TASK_CONFIG.update({'name':  'oauth_emailbackend_using_celery', 
                        'ignore_result': True,
                        'rate_limit':    '30/m', # 분당 발송 건수 --2초 delay... 차후 다시 확인할 것 worker 단위 적용. 프로세스(concurrenty) 갯수와는 상관없음 
                        })

    # import base if string to allow a base celery task
    if 'base' in TASK_CONFIG and isinstance(TASK_CONFIG['base'], string_types):
        from django.utils.module_loading import import_string
        TASK_CONFIG['base'] = import_string(TASK_CONFIG['base'])

    @shared_task(**TASK_CONFIG) 
    def celery_send_emails(messages, 
                           emailclient_id,
                           using='default',
                           backend_kwargs=None, 
                           retry_count=0,
                           **kwargs):
        """
        @using : 공용 celery 서버로 이용하여 각 사이트에서 이메일을 발송할 때 celery 서버에서 접속할 database를 달리할 수 있다.
        """
        if emailclient_id:
            emailclient = EmailClient.objects.using(using).get(id=emailclient_id)
        else:
            emailclient = EmailClient()

        if isinstance(messages, (EmailMessage, dict)):
            messages = [messages]

        messages = [email_to_dict(m) for m in messages]
        
        
        combined_kwargs = {
            "emailclient_id": emailclient_id,
        }
        combined_kwargs.update(backend_kwargs)


        retry_kwargs = {
                    'history_pk': 1,
                    'backend_kwargs': backend_kwargs,
                    'retry_count': retry_count + 1
                    }
        retry_kwargs.update(kwargs)   
            
        # conn는 EMAIL_BACKEND 인스턴스 임 
        # EMAIL_BACKEND의 connection이 아님 
        conn = get_connection(backend=settings.EMAIL_BACKEND, **combined_kwargs)
        try:
            conn.open(emailclient)
        except Exception:
            if emailclient.debug:
                logger.exception("Cannot reach EMAIL_BACKEND %s", settings.EMAIL_BACKEND)

        num_sent = 0
        for message in messages:
            try:
                # 다시 EmailMessage로 변환 
                msg  = dict_to_email(message)
                # Celery를 실행하지 않도록 한다.
                print('* tasks.send_messages emailclient_id = %s' % emailclient_id)
                sent = conn.send_messages([msg], enable_celery=False)
                if sent is not None:
                    num_sent += sent
                if emailclient.debug:
                    logger.debug("Successfully sent email message to %r.", message['to'])
            except Exception as e:
                if emailclient.debug:
                    logger.warning("Failed to send email message to %r, retrying. (%r)", message['to'], e)
                
                print(">>>>>Try retry")
                ret = celery_send_emails.retry(args=(message, str(emailclient.id), using), 
                                        kwargs=retry_kwargs,
                                        exc=e, 
                                        throw=False,
                                        countdown=1*60, # after 3 seconds
                                        max_retries=10,)
                print("<<<<< Retry: %r" % ret)


                # # 재시도 횟수가 max_retiries에 도달하여 관리자에게 문자 발송 
                # if retry_kwargs['retry_count'] == 9:
                #     print(">>>ITSM INCIDENT MESSAGE SENDING..., %r" % settings.ITSM_INCIDENT_RECEIVERS)
                    
                #     subject = '%r투고시스템 이메일 발송 재시도 횟수가 10회에 도달하였습니다. \n\n%r' % (site, ret)
                #     resp = send_itsm_incident_message(subject, None, send_type='LM')
                #     print(">>>ITSM INCIDENT MESSAGE SENT, %r" % resp)

        conn.close()
        return num_sent

    try:
        from celery.utils.log import get_task_logger
        logger = get_task_logger(__name__)
    except ImportError:
        logger = celery_send_emails.get_logger()

except ImportError:
    pass