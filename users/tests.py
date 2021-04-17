import os
import re
import uuid

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import mail
from users.models import PendingEmail


User = get_user_model()

NORMAL = 'normal@user.com'
ABINORMAL = 'abinormal@user.com'
test_pw = 'foo'


def get_local_user(e=NORMAL, subscribed=True):
    User.objects.filter(email=e).delete()
    return User.objects.create_user(email=e, password=test_pw, subscribed=subscribed, display_name='dn')


def remove_abinormal():
    User.objects.filter(email=ABINORMAL).delete()


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
            User.objects.create_user(email='', password=test_pw)

    def test_create_superuser(self):
        su = "super@user.com"
        User = get_user_model()
        admin_user = User.objects.create_superuser(su, test_pw)
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
                email=su, password=test_pw, is_superuser=False)

    def test_profile(self):
        user = get_local_user()
        client = Client()
        client.login(email=NORMAL, password=test_pw)
        path = reverse('profile')
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')

        data = {'email': NORMAL, 'first_name': 'Iam', 'last_name': 'Normal',
                'location': 'Turkey', 'display_name': user.display_name}
        response = client.post(path, data=data)
        self.assertEqual(response.reason_phrase, 'OK')

        user = User.objects.get(email=NORMAL)
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.location, data['location'])

    def test_display_name_from_first_and_last(self):
        new_user = User.objects.create_user(
            email="test@oauthuser.com",
            first_name="first",
            last_name="last"
        )
        self.assertEqual(new_user.display_name, "first last")

    def test_first_and_last_from_display_name(self):
        new_user = User.objects.create_user(
            email="test@avgplayer.com",
            display_name="notice me 😱 i'm complicated",
            last_name="last"
        )
        self.assertEqual(new_user.first_name, "notice")
        self.assertEqual(new_user.last_name, "me 😱 i'm complicated")

    def test_logout(self):
        # Make sure user exists.
        get_local_user()

        client = Client()
        logged_in = client.login(email=NORMAL, password=test_pw)
        self.assertTrue(logged_in)
        logged_in = client.logout()
        self.assertEqual(logged_in, None)

    def test_password_change(self):
        # Make sure user exists.
        get_local_user()

        mail.outbox = []

        client = Client()
        client.login(email=NORMAL, password=test_pw)
        path = reverse('password_change')
        response = client.get(path)
        self.assertIn(response.status_code, [200, 302])

        path = reverse('password_change')
        pw = 'nAPrZuTg9pr8dLN2'

        response = client.post(path, {'old_password': test_pw, 'new_password1': pw, 'new_password2': pw})
        self.assertIn(response.status_code, [200, 302])

        logged_in = client.logout()
        self.assertEqual(logged_in, None)
        logged_in = client.login(email=NORMAL, password=pw)
        self.assertTrue(logged_in)

    def test_forgot_password(self):
        # Make sure user exists.
        get_local_user()

        client = Client()
        logged_in = client.login(email=NORMAL, password=test_pw)
        self.assertEqual(logged_in, True)

        response = client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name[0], 'users/pwd_reset.html')

        mail.outbox = []
        response = client.post(reverse('password_reset'), {'email': NORMAL})
        self.assertIn(response.status_code, [200, 302])

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Commonology password reset')

        token = response.context[0]['token']
        uid = response.context[0]['uid']

        response = client.get(reverse('password_reset_confirm',
                                      kwargs={'token': token, 'uidb64': uid}))
        self.assertIn(response.status_code, [200, 302])

        # Now we post to the same url with our new password:
        path = reverse('password_reset_confirm',
                       kwargs={'token': token, 'uidb64': uid})
        response = client.post(path, {'new_password1': test_pw, 'new_password2': test_pw})
        self.assertIn(response.status_code, [200, 302])


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
        self.assertIn(response.status_code, [200, 302])
        x = User.objects.filter(email__exact=data['email']).exists()
        self.assertEqual(x, flag)

    def test_invite(self):
        user = get_local_user()
        remove_abinormal()

        self.assertEqual(test_pw, 'foo')
        client = Client()
        result = client.login(email=NORMAL, password=test_pw)
        self.assertTrue(result)

        mail.outbox = []
        url = reverse('invite')
        response = client.post(url, data={"emails": ABINORMAL})
        self.assertIn(response.status_code, [200, 302])

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
        data['password2'] = test_pw
        self.assert_user_was_created(path, data, False)

        data['password2'] = data['password1']
        self.assert_user_was_created(path, data, True)

        remove_abinormal()

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
            remove_abinormal()

    def test_join(self):
        data = self.data

        self.join_test_helper(data, taint_uuid_flag=True)

        data['password2'] = test_pw
        self.join_test_helper(data)
        data['password2'] = data['password1']

        self.join_test_helper(data)

    def test_email_change(self):
        user = get_local_user()
        client = Client()
        client.login(email=NORMAL, password=test_pw)
        path = reverse('profile')
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')

        data = {'email': ABINORMAL, 'first_name': 'Iam', 'last_name': 'Normal',
                'location': 'Turkey', 'display_name': user.display_name}
        mail.outbox = []
        response = client.post(path, data=data)
        self.assertEqual(response.reason_phrase, 'OK')

        flag = User.objects.filter(email__exact=ABINORMAL).exists()
        self.assertFalse(flag)

        msg = mail.outbox[0].body
        url = re.search("(?P<url>https?://[^\s]+)", msg).group("url")
        mail.outbox = []

        response = client.get(url)
        self.assertIn(response.status_code, [302, 404])

        flag = User.objects.filter(email__exact=ABINORMAL).exists()
        self.assertTrue(flag)

        flag = User.objects.filter(email__exact=NORMAL).exists()
        self.assertFalse(flag)

        remove_abinormal()
