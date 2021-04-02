from django.test import TestCase
from django.conf import settings


class ProjectTestCase(TestCase):
    settings.MAILCHIMP_EMAIL_LIST_ID = None
