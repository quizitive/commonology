from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from game.tests import suppress_hidden_error_logs


class TestContact(TestCase):
    @suppress_hidden_error_logs
    def test_contact(self):
        c = Client()
        path = reverse('contact')
        mail.outbox = []
        data = {'from_email': 'ms@quizitive.com', 'destination': '2', 'message': 'hello'}
        response = c.post(path, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank you, we hope to reply today or early tomorrow.")
        msg = mail.outbox[0].body
        self.assertEqual(msg,
                         'Contact Form -- ms@quizitive.com sent this message with subject: Investor Relations\nhello')
        mail.outbox = []
