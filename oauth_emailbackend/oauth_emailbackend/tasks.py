from django.conf import settings
from six import string_types
from django.core.mail import EmailMessage, get_connection
from .utils import add_send_history, dict_to_email, email_to_dict, mark_send_history, mark_send_history_by_instance 
from .models import EmailClient

try:
    from celery import shared_task

    CELERY_MAX_RETRY= getattr(settings, "OAUTH_EMAILBACKEND_CELERY_MAX_RETRY", 3)

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
            message_id  = message['headers']['Message-ID']
            msg         = dict_to_email(message)

            print('message_id:', message_id)

            if retry_count == 0 and emailclient.site:
                history_obj = add_send_history(message_id, emailclient.site, msg, using=emailclient.using)

            try:
                # 다시 EmailMessage로 변환 
                sent = conn.send_messages([msg], enable_celery=False)
                print('*** sent:', sent)
                if sent:
                    num_sent += sent
                # if emailclient.site:
                #     mark_send_history_by_instance(history_obj, bool(sent))
                
                if emailclient.debug:
                    logger.debug("Successfully sent email message to %r.", message['to'])
            except Exception as e:
                if emailclient.debug:
                    logger.warning("Failed to send email message to %r, retrying. (%r)", message['to'], e)
                
                    if retry_count > CELERY_MAX_RETRY:
                        logger.warning("Sending emails to %r was stopped because the maximum number of attempts was %d.", message['to'], CELERY_MAX_RETRY)
                if emailclient.site:
                    mark_send_history_by_instance(history_obj, False, str(e), retry_count)

                if retry_count > CELERY_MAX_RETRY:
                    # [TODO] send history에 최종 발송 오류 표시 
                    continue 

                ret = celery_send_emails.retry(args=(message, str(emailclient.id), using), 
                                        kwargs=retry_kwargs,
                                        exc=e, 
                                        throw=False,
                                        countdown=1*10, # after 60 seconds
                                        max_retries=CELERY_MAX_RETRY,)
                print(">>> Retry: %r" % ret)

        conn.close()
        return num_sent

    try:
        from celery.utils.log import get_task_logger
        logger = get_task_logger(__name__)
    except ImportError:
        logger = celery_send_emails.get_logger()

except ImportError:
    pass