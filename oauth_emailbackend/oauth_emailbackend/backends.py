from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from .tasks import send_emails
from .utils import chunked, email_to_dict



class OAuthEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super(OAuthEmailBackend, self).__init__(fail_silently)
        self.init_kwargs = kwargs

    def send_messages(self, email_messages):
        #import inspect
        #print(inspect.getmodule(send_emails).__name__)
        
        ''' by odop 2018.11.14 '''
        # site 특정하여 발송 가능하도록 처리 
        site_id = settings.SITE_ID
        
        test = email_messages[0]
        if hasattr(test, 'site'):
            site_id = test.site.id
            
        ''' by odop 2019.8.24 '''
        # 특정 데이터베이스와 이메일 호스트를 지정하여 이메일을 발송할 수 있도록 수정 
        
        email_server_name = getattr( test, 'email_server_name', 'default')
        email_server_database = getattr( test, 'email_server_database', getattr(settings, 'OAUTH_EMAILBACKEND_DBNAME', 'default')) 
        
        
        result_tasks = []
        messages = [email_to_dict(msg) for msg in email_messages]
        for chunk in chunked(messages, settings.CELERY_EMAIL_CHUNK_SIZE):
            result_tasks.append(send_emails.delay(chunk, site_id, 
                                                  email_server_name=email_server_name,
                                                  email_server_database=email_server_database,
                                                  backend_kwargs=self.init_kwargs))
        return result_tasks
