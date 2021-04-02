import os
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from users.tests import get_local_user, NORMAL
from django.contrib.auth import get_user_model
from project.bases import ProjectTestCase
from .mailchimp_utils import Mailchimp
from .tasks import update_mailing_list
from django.conf import settings


class GithubSecretTests(TestCase):
    def test_secret(self):
        api_key = os.getenv('API_KEY')
        self.assertEqual(api_key, 'Marc Schwarzschild')


class MailchimpHookTests(ProjectTestCase):
    def test_mailchimphook(self):
        u = get_local_user()
        self.assertTrue(u.subscribed)
        uu = os.getenv('MAILCHIMP_HOOK_UUID')
        client = Client()
        path = reverse('mailchimp_hook', kwargs={'uuid': uu})
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
        self.mc_client.make_list_baseurl(self.list_id)
        self.assertEqual(status_code, 200)

    def tearDown(self):
        list_id = self.mc_client.delete_list_by_name(self.list_name)
        self.assertEqual(type(list_id), str)

    def test_ping(self):
        response = self.mc_client.ping()
        self.assertEqual(response, "Everything's Chimpy!")

    def assert_mail_status(self, email, status):
        status_code, members = self.mc_client.get_members()
        self.assertEqual(status_code, 200)
        self.assertIn(email, members)
        subscribe_status = members[email]
        self.assertEqual(subscribe_status, status)

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

        update_mailing_list(email, is_subscribed=False)
        self.assert_mail_status(email, 'unsubscribed')

        update_mailing_list(email)
        self.assert_mail_status(email, 'subscribed')

        status_code = self.mc_client.delete_permanent(email)
        self.assertEqual(status_code, 204)

        # Test subscribe when contact has not already been added to the list.
        email = f'moe{str(uuid.uuid4().int)}@foo.com'
        status_code, status = self.mc_client.subscribe(email)
        self.assertEqual(status_code, 200)
        self.assertEqual(status, 'subscribed')
