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
        self.client = Client()

    def test_series_permissions_leaderboard(self):
        # make a private leaderboard
        series = Series.objects.create(name="Series 1", slug="series-1")
        self.game.series = series
        self.game.save()
        url = reverse('series-leaderboard:default', kwargs={'series_slug': series.slug})
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (403, 302))

        # make a user that plays the series
        user = get_local_user()
        series.players.add(user)
        self.client.login(email=user.email, password=test_pw)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
