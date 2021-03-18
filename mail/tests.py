import os
from django.test import TestCase, Client
from django.urls import reverse

# https://github.com/mailchimp/mailchimp-marketing-python
import mailchimp_marketing as MailchimpMarketing


# log into your Mailchimp account and look at the URL in your browser.
# You’ll see something like https://us19.admin.mailchimp.com/
# the us19 part is the server prefix.
SERVER_PREFIX = 'us2'


class GithubSecretTests(TestCase):
    def test_secret(self):
        api_key = os.getenv('API_KEY')
        self.assertEqual(api_key, 'Marc Schwarzschild')


class MailchimpTests(TestCase):
    def test_ping(self):
        api_key = os.getenv('MAILCHIMP_APIKEY')
        try:
            client = MailchimpMarketing.Client()
            client.set_config({
                "api_key": api_key,
                "server": SERVER_PREFIX
            })
            response = client.ping.get()
            self.assertEqual(response['health_status'], "Everything's Chimpy!")
        except MailchimpMarketing.api_client.ApiClientError:
            self.assertTrue(False, msg="Mailchimp API failing to connect.")

    def test_mailchimphook(self):
        uuid = os.getenv('MAILCHIMP_HOOK_UUID')
        client = Client()
        path = reverse('mailchimp_hook', kwargs={'uuid': uuid})
        data = {'type': ['unsubscribe'], 'fired_at': ['2021-03-17 14:16:55'], 'data[action]': ['unsub'],
                'data[reason]': ['manual'], 'data[id]': ['96b581d0ae'], 'data[email]': ['ms@koplon.com'],
                'data[email_type]': ['html'], 'data[ip_opt]': ['100.16.130.45'], 'data[web_id]': ['1362500348'],
                'data[merges][EMAIL]': ['ms@koplon.com'], 'data[merges][FNAME]': ['Marc'],
                'data[merges][LNAME]': ['Schwarzschild'], 'data[merges][ADDRESS]': [''], 'data[merges][PHONE]': [''],
                'data[list_id]': ['36b9567454']}
        response = client.post(path, data=data)
        self.assertEqual(response.reason_phrase, 'OK')
