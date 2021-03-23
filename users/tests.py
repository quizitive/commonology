import os
import re
import uuid
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import mail
from users.models import PendingEmail, USER_CLASS


NORMAL = 'normal@user.com'
ABINORMAL = 'abinormal@user.com'
local_user = None


def get_local_user(reset=False):
    global local_user
    if reset:
        try:
            USER_CLASS.objects.get(email=NORMAL).delete()
        except USER_CLASS.DoesNotExist:
            pass
        local_user = None
    if local_user is None:
        User = get_user_model()
        local_user = User.objects.create_user(email=NORMAL, password='foo')
    return local_user


class MailTests(TestCase):

    def test_sendmail(self):
        mail.outbox = []
        mail.send_mail(subject='testing', from_email=ABINORMAL, recipient_list=[NORMAL], message='')
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox = []


class UsersManagersTests(TestCase):

    def test_create_user(self):
        User = get_user_model()
        user = get_local_user()
        self.assertEqual(user.email, NORMAL)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email='')
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password="foo")

    def test_create_superuser(self):
        su = "super@user.com"
        User = get_user_model()
        admin_user = User.objects.create_superuser(su, 'foo')
        self.assertEqual(admin_user.email, su)
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email=su, password='foo', is_superuser=False)

    def test_profile(self):
        user = get_local_user()
        client = Client()
        client.login(email=NORMAL, password='foo')
        path = reverse('profile')
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')

        data = {'email': NORMAL, 'first_name': 'Iam', 'last_name': 'Normal', 'location': 'Turkey'}
        response = client.post(path, data=data)
        self.assertEqual(response.reason_phrase, 'OK')

        user = USER_CLASS.objects.get(email=NORMAL)
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.location, data['location'])

    def test_logout(self):
        # Make sure user exists.
        get_local_user(reset=True)

        client = Client()
        logged_in = client.login(email=NORMAL, password='foo')
        self.assertTrue(logged_in)
        logged_in = client.logout()
        self.assertEqual(logged_in, None)

    def test_password_change(self):
        # Make sure user exists.
        get_local_user(reset=True)

        mail.outbox = []

        client = Client()
        client.login(email=NORMAL, password='foo')
        path = reverse('password_change')
        response = client.get(path)
        self.assertIn(response.reason_phrase, ['OK', 'Found'])

        path = reverse('password_change')
        pw = 'nAPrZuTg9pr8dLN2'

        response = client.post(path, {'old_password': 'foo', 'new_password1': pw, 'new_password2': pw})
        self.assertEqual(response.status_code, 302)

        logged_in = client.logout()
        self.assertEqual(logged_in, None)
        logged_in = client.login(email=NORMAL, password=pw)
        self.assertTrue(logged_in)

    def test_forgot_password(self):
        # Make sure user exists.
        get_local_user(reset=True)

        client = Client()
        logged_in = client.login(email=NORMAL, password='foo')
        self.assertEqual(logged_in, True)

        response = client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name[0], 'users/pwd_reset.html')

        mail.outbox = []
        response = client.post(reverse('password_reset'), {'email': NORMAL})
        self.assertEqual(response.status_code, 302)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Commonology password reset')

        token = response.context[0]['token']
        uid = response.context[0]['uid']

        response = client.get(reverse('password_reset_confirm', kwargs={'token': token, 'uidb64': uid}))
        self.assertEqual(response.reason_phrase, 'Found')

        # Now we post to the same url with our new password:
        path = reverse('password_reset_confirm',
                       kwargs={'token': token, 'uidb64': uid})
        response = client.post(path, {'new_password1': 'foo', 'new_password2': 'foo'})
        self.assertEqual(response.status_code, 302)


class PendingUsersTests(TestCase):

    def setUp(self):
        pw = '3CgAQCHzyv5x5yhN'
        self.data = {'email': ABINORMAL,
                     'first_name': 'Abi',
                     'last_name': 'Normal',
                     'display_name': 'abnormal',
                     'location': 'Andorra',
                     'referrer': NORMAL,
                     'password1': pw,
                     'password2': pw}

    def assert_user_was_created(self, path, data, flag):
        client = Client()
        response = client.post(path, data=data)
        self.assertIn(response.reason_phrase, ['OK', 'Found'])
        x = USER_CLASS.objects.filter(email__exact=data['email']).exists()
        self.assertEqual(x, flag)

    def test_invite(self):
        user = get_local_user()

        client = Client()
        client.login(email=NORMAL, password='foo')
        mail.outbox = []
        response = client.post(reverse('invite'), data={"email": ABINORMAL})
        self.assertEqual(response.reason_phrase, 'OK')

        pe = PendingEmail.objects.get(email=ABINORMAL)
        self.assertEqual(NORMAL, pe.referrer)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(pe.uuid), mail.outbox[0].body)
        mail.outbox = []

        client = Client()
        path = reverse('join') + str(pe.uuid)
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')

        data = self.data
        data['password2'] = 'foo'
        self.assert_user_was_created(path, data, False)

        data['password2'] = data['password1']
        self.assert_user_was_created(path, data, True)

        USER_CLASS.objects.get(email=ABINORMAL).delete()

    def join_test_helper(self, data, taint_uuid_flag=False):
        client = Client()
        response = client.post(reverse('join'), data={"email": ABINORMAL})
        self.assertEqual(response.reason_phrase, 'OK')

        msg = mail.outbox[0].body
        url = re.search("(?P<url>https?://[^\s]+)", msg).group("url")
        base_url, uuid_str = url.rsplit('/', 1)

        mail.outbox = []

        flag = True
        if taint_uuid_flag:
            uuid_str = str(uuid.uuid4())
            flag = False

        path = os.path.join(base_url, uuid_str)

        if data['password1'] != data['password2']:
            flag = False

        self.assert_user_was_created(path, data, flag)

        if flag:
            USER_CLASS.objects.get(email=ABINORMAL).delete()

    def test_join(self):
        data = self.data

        self.join_test_helper(data, taint_uuid_flag=True)

        data['password2'] = 'foo'
        self.join_test_helper(data)
        data['password2'] = data['password1']

        self.join_test_helper(data)

    def test_inhibited_join(self):
        os.environ['INHIBIT_JOIN_VIEW'] = 'True'
        client = Client()
        path = reverse('join')
        response = client.get(path)
        self.assertEqual(response.url, '/')
        self.assertEqual(response.reason_phrase, 'Found')

        del os.environ['INHIBIT_JOIN_VIEW']
        client = Client()
        path = reverse('join')
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')
