import os
from django.test import TestCase, Client
from django.urls import reverse
from users.tests import get_local_user, NORMAL
from django.contrib.auth import get_user_model
from .mailchimp_utils import Mailchimp
from project.settings import MAILCHIMP_SERVER, MAILCHIMP_API_KEY


# ID for Audience named Marc
MAILCHIMP_TEST_LIST_ID='36b9567454'

class GithubSecretTests(TestCase):
    def test_secret(self):
        api_key = os.getenv('API_KEY')
        self.assertEqual(api_key, 'Marc Schwarzschild')

class MailchimpHookTests(TestCase):
    def test_mailchimphook(self):
        u = get_local_user()
        self.assertTrue(u.subscribed)
        uuid = os.getenv('MAILCHIMP_HOOK_UUID')
        client = Client()
        path = reverse('mailchimp_hook', kwargs={'uuid': uuid})
        data = {'type': ['unsubscribe'], 'fired_at': ['2021-03-17 14:16:55'], 'data[action]': ['unsub'],
                'data[reason]': ['manual'], 'data[id]': ['96b581d0ae'], 'data[email]': [NORMAL],
                'data[email_type]': ['html'], 'data[ip_opt]': ['100.16.130.45'], 'data[web_id]': ['1362500348'],
                'data[merges][EMAIL]': ['ms@koplon.com'], 'data[merges][FNAME]': ['Marc'],
                'data[merges][LNAME]': ['Schwarzschild'], 'data[merges][ADDRESS]': [''], 'data[merges][PHONE]': [''],
                'data[list_id]': ['36b9567454']}
        response = client.post(path, data=data)
        self.assertEqual(response.reason_phrase, 'OK')
        User = get_user_model()
        u = User.objects.get(email=NORMAL)
        self.assertFalse(u.subscribed)


class MailchimpAPITests(TestCase):

    def setUp(self):
        self.mc_client = Mailchimp(MAILCHIMP_SERVER, MAILCHIMP_API_KEY, MAILCHIMP_TEST_LIST_ID)
        self.user = get_local_user()
        self.mc_client.subscribe(self.user.email)

    def test_ping(self):
        response = self.mc_client.ping()
        j = response.json()
        self.assertEqual(j['health_status'], "Everything's Chimpy!")

    def test_getmembers(self):
        status_code, members = self.mc_client.get_members()
        print(members)  #...

    def test_deletemember(self):
        status_code, j = self.mc_client.add_list('marc_testing')
        print(status_code)
        print(j)
        return

        email = 'foo@quizitive.com'
        status_code, j = self.mc_client.add_member_to_list(email)
        print(status_code)
        print(j)
        status_code, j = self.mc_client.delete_member('foo@quizitive.com')
        print(status_code)
        print(j)


    def test_getmemberinfo(self):
        pass # ...

    def test_unsubscribe(self):
        # test resubscribe here
        # test delete list member
        pass # ...



    def test_getlist(self):
        email = 'foo@quizitive.com'
        response = self.mc_client.subscribe(email)
        pass

    def test_subscribe(self):
        email = 'foo@quizitive.com'
        #email = 'ms@brookhavenstrategies.com'
        m = self.mc_client
        x = m.ping()
        # x = m.get_members()
        #x = m.unsubscribe(email)
        #x = m.resubscribe(email)
        #x = m.add_email(email)
        print(x)

