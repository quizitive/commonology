import os
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from users.tests import get_local_user, NORMAL
from django.contrib.auth import get_user_model
from .mailchimp_utils import Mailchimp
from project import settings


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
        self.mc_client = Mailchimp(settings.MAILCHIMP_SERVER, settings.MAILCHIMP_API_KEY)
        self.list_name = 'marc_testing'

        self.mc_client.delete_list_by_name(self.list_name)
        status_code, self.list_id = self.mc_client.add_list(self.list_name)
        settings.MAILCHIMP_EMAIL_LIST_ID = self.list_id
        self.assertEqual(status_code, 200)

    def tearDown(self):
        list_id = self.mc_client.delete_list_by_name(self.list_name)
        self.assertEqual(type(list_id), str)

    def test_ping(self):
        response = self.mc_client.ping()
        j = response.json()
        self.assertEqual(j['health_status'], "Everything's Chimpy!")

    def assert_mail_status(self, email, status):
        status_code, members = self.mc_client.get_members()
        self.assertEqual(status_code, 200)
        self.assertIn(email, members)
        subcribe_status = members[email]
        self.assertEqual(subcribe_status, status)

    def test_member(self):
        email = f'moe{str(uuid.uuid4().int)}@foo.com'

        status_code, status = self.mc_client.add_member_to_list(email)
        self.assertEqual(status_code, 200)
        self.assertEqual(status, 'subscribed')

        self.assert_mail_status(email, 'subscribed')

        status_code, status = self.mc_client.unsubscribe(email)
        self.assertEqual(status_code, 200)
        self.assertEqual(status, 'unsubscribed')

        status_code, status = self.mc_client.subscribe(email)
        self.assertEqual(status_code, 200)
        self.assertEqual(status, 'subscribed')

        status_code = self.mc_client.delete_permanent(email)
        self.assertEqual(status_code, 204)

        # Test subscribe when contact has not already been added to the list.
        email = f'moe{str(uuid.uuid4().int)}@foo.com'
        status_code, status = self.mc_client.subscribe(email)
        self.assertEqual(status_code, 200)
        self.assertEqual(status, 'subscribed')

    def test_player_save_signal(self):
        print(f"Test List ID: {self.mc_client.list_id}")
        print('About to save.')
        u = get_local_user()
        self.assert_mail_status(u.email, 'subscribed')

        print('About to save again.')
        u = get_local_user(subscribed=False)
        self.assert_mail_status(u.email, 'unsubscribed')
