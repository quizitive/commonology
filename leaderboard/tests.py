from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from game.models import Game
from game.tests import BaseGameDataTestCase


class TestHTMXLeaderboard(BaseGameDataTestCase):

    def setUp(self):
        self.game.publish = True
        self.game.save()
        self.client = Client()
        self.su_email = "super@user.com"
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(self.su_email, 'foo')

    def _assert_code(self, url, code):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code)

    def test_leaderboard_view(self):
        url = reverse('leaderboard')
        self._assert_code(url, 200)

    def test_leaderboard_game_view(self):
        # non-staff user can't see other weeks directly
        url = reverse('leaderboard-game', kwargs={'game_id': 1})
        self._assert_code(url, 404)

    def test_htmx_leaderboard_resp(self):
        # most recent game is public
        url = reverse('leaderboard-htmx')
        pub_resp = self.client.get(url)
        self.assertEqual(pub_resp.status_code, 200)

        # non-staff always get most recent leaderboard via htmx
        new_game = Game.objects.create(publish=False)
        resp = self.client.get(url, {'game_id': new_game.game_id})
        self.assertEqual(pub_resp.content, resp.content)

        # staff users can access games if they exist
        self.client.login(email=self.su_email, password='foo')
        staff_resp = self.client.get(url, {'game_id': new_game.game_id})
        self.assertEqual(staff_resp.status_code, 200)
        self.assertNotEqual(staff_resp.content, pub_resp.content)
