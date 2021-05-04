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
        self.user = get_local_user()
        self.authenticated_client = Client()
        self.authenticated_client.login(email=self.user.email, password=test_pw)

    def test_player_home(self):
        url = reverse('player-home')
        resp = self.authenticated_client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_series_permissions_leaderboard(self):
        # make a private leaderboard
        series = Series.objects.create(name="Series 1", slug="series-1", owner=self.user)
        self.game.series = series
        self.game.save()
        url = reverse('series-leaderboard:default', kwargs={'series_slug': series.slug})
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (403, 302))

        # a user that is a player of the series can view
        resp = self.authenticated_client.get(url)
        self.assertEqual(resp.status_code, 200)
