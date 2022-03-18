import os
import re
import uuid

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings
from users.models import PendingEmail, Player
from users.utils import sign_user
from game.models import Series, Answer, Question


User = get_user_model()

NORMAL = 'normal@user.com'
ABINORMAL = 'abinormal@user.com'
test_pw = 'foo'


def get_local_user(e=NORMAL, subscribed=True, pw=test_pw):
    User.objects.filter(email=e).delete()
    u = User.objects.create_user(email=e, subscribed=subscribed, display_name='dn')
    if pw:
        u.set_password(pw)
        u.save()
    return u


def get_local_client(e=NORMAL, pw=test_pw):
    c = Client()
    c.login(email=e, password=pw)
    return c


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
        with self.assertRaises(ValueError):
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
        client = get_local_client()
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

        client = get_local_client()
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

    def test_unsubscribe_link(self):
        user = get_local_user()
        id = user.code

        saved_key = settings.SECRET_KEY
        settings.SECRET_KEY = 'Test'

        token = sign_user(user, id)
        self.assertEqual(token, f"{id}:0s9kU4sbRep-eXx01wMXH7dfp84JlIrkIxEJpAstUnI")

        self.assertTrue(user.subscribed)
        client = Client()

        mail.outbox = []
        url = reverse('unsubscribe', kwargs={'token': token})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        email = user.email
        user = User.objects.get(email=email)
        self.assertFalse(user.subscribed)

        msg = mail.outbox[0].body
        url = re.search("HTTPS.*://.*/subscribe/.*\"", msg).group(0)[:-1]
        base_url, token = url.rsplit('/', 1)
        response = client.get(reverse('subscribe', kwargs={'token': token}))
        self.assertEqual(response.status_code, 200)
        user = User.objects.filter(email=user.email).get()
        self.assertTrue(user.subscribed)

        # Trying a bad unsubscribe url
        mail.outbox = []
        url += 'foo'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email=email)
        self.assertContains(response, "There is something wrong with the link you used.")
        self.assertTrue(user.subscribed)

        settings.SECRET_KEY = saved_key

    def test_following_self(self):
        user = get_local_user()
        self.assertEqual(1, user.following.count())

    def test_display_name(self):
        user = User.objects.create(email="p@test.com", first_name="F", last_name="P")
        self.assertEqual("F P", user.display_name)


class PendingUsersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        owner = get_local_user(e='series@owner.com')
        Series.objects.create(name="Commonology", owner=owner, public=True)

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
        if flag:
            p = User.objects.get(email=data['email'])
            self.assertTrue(p.series.filter(slug='commonology').exists())

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
        self.assertEqual(Player.objects.get(email=NORMAL), pe.referrer)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(pe.uuid), mail.outbox[0].body)
        mail.outbox = []

        client = Client()

        # test unsubscribe from invite
        path = reverse('unsubscribe', kwargs={'token': 'None:' + str(pe.uuid)})
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')

        path = reverse('join') + str(pe.uuid)
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')

        x = User.objects.filter(email__exact=ABINORMAL).exists()
        self.assertEqual(x, True)

        remove_abinormal()

    def join_test_helper(self, data, taint_uuid_flag=False):
        client = Client()
        response = client.post(reverse('join'), data={"email": data['email']})
        self.assertEqual(response.reason_phrase, 'OK')

        msg = mail.outbox[0].body
        url = re.search("https?://.*/join/.*\"", msg).group(0)[:-1]
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

    def test_join_email_exists(self):
        data = self.data
        email = data['email']
        get_local_user(e=email)
        self.join_test_helper(data)

        get_local_user(e=email, pw=None)
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
        url = re.search("change: (?P<url>https?://[^\s]+)", msg).group("url")
        mail.outbox = []

        response = client.get(url)
        self.assertIn(response.status_code, [302, 404])

        flag = User.objects.filter(email__exact=ABINORMAL).exists()
        self.assertTrue(flag)

        flag = User.objects.filter(email__exact=NORMAL).exists()
        self.assertFalse(flag)

        remove_abinormal()

    def test_join_bad_email(self):
        client = Client()
        response = client.post(reverse('join'), data={"email": 'foo@goo.con'})
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, "ends with .con and probably should be .com")

    def test_referral_count(self):
        user1 = get_local_user()
        user2 = get_local_user(e='igot@referred.com')
        user2.referrer = user1
        user2.save()

        # not a referral until they play a game
        self.assertEqual(user1.players_referred.count(), 0)

        # give them an answer
        q = Question.objects.create(text='question text')
        Answer.objects.create(player=user2, raw_string='answer', question=q)
        self.assertEqual(user1.players_referred.count(), 1)

    def test_email_join_referral(self):
        user1 = get_local_user()
        referred_email = 'igot@referred.com'
        pe = PendingEmail.objects.create(referrer=user1, email=referred_email)

        join_view = reverse('join', args=[pe.uuid])
        Client().get(join_view)
        user2 = Player.objects.get(email=referred_email)

        self.assertTrue(user1 in user2.following.all())
        self.assertTrue(user2 in user1.following.all())


class LoginTests(TestCase):
    def test_with_password(self):
        user = get_local_user()
        client = Client()
        is_logged_in = client.login(email=NORMAL, password=test_pw)
        self.assertTrue(is_logged_in)

    def test_without_password(self):
        user = get_local_user()

        mail.outbox = []

        client = Client()
        response = client.post(reverse('login'), data={"username": user.email})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"An email validation link was sent to {user.email}.")

        msg = mail.outbox[0].body

        url = re.search("https?://.*(?P<uidb64>\/validate_email\/[^\s]+)\/\"\>", msg).group("uidb64")
        mail.outbox = []

        response = client.get(url, follow=True)
        u, c = response.redirect_chain[1]
        self.assertEqual(c, 302)
        self.assertEqual(u, '/leaderboard/')


class MergePlayers(TestCase):
    def test_fields(self):
        # This test is designed to make sure we maintain merge_players.py
        # when new Player related fields are added.

        expected = ['referrals', 'followers', 'pendingemail', 'captain_teams', 'teams',
                    'logentry', 'social_auth', 'comments', 'owned_series', 'hosted_series',
                    'series', 'hosted_games', 'answers', 'claim', 'mailingaddress',
                    'id', 'password', 'last_login', 'is_superuser', 'is_staff', 'is_active', 'date_joined',
                    'email', 'first_name', 'last_name', 'location', 'birth_date', 'subscribed', '_code',
                    'reminder', 'referrer', 'display_name', 'is_member', 'data', 'groups', 'user_permissions',
                    'following', 'rank_scores']

        names = [field.name for field in Player._meta.get_fields()]
        self.assertTrue(set(names) == set(expected),
                        msg='Was a model changed that relates to Player? Check impact to scripts/hacks/merge_players.py')
