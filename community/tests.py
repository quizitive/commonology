from django.test import TestCase
from django.urls import reverse
from django.test import Client

from game.models import Series
from game.tests import BaseGameDataTestCase
from users.tests import get_local_user, test_pw


class TestCommunityViews(BaseGameDataTestCase):

    def setUp(self):
        self.game.publish = True
        self.game.save()
        self.authenticated_client = Client()
        self.authenticated_client.login(email=self.game_player.email, password=test_pw)

    def test_player_home(self):
        url = reverse('player-home')
        resp = self.authenticated_client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_series_permissions_leaderboard(self):
        # make the series private
        self.series.public = False
        self.series.save()
        url = reverse('series-leaderboard:default', kwargs={'series_slug': self.series.slug})
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (403, 302))

        # a logged in user that is not a player of the series cannot view
        resp = self.authenticated_client.get(url)
        self.assertEqual(resp.status_code, 403)

        # but if they're a player, they can view
        self.series.players.add(self.game_player)
        resp = self.authenticated_client.get(url)
        self.assertEqual(resp.status_code, 200)
