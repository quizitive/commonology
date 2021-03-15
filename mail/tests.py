import os
from django.test import TestCase
from django.http import HttpResponse


# https://github.com/mailchimp/mailchimp-marketing-python
import mailchimp_marketing as MailchimpMarketing


# log into your Mailchimp account and look at the URL in your browser.
# You’ll see something like https://us19.admin.mailchimp.com/
# the us19 part is the server prefix.
SERVER_PREFIX = 'us2'


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
            return HttpResponse("Mailchimp API failing to connect.")
