from django.urls import reverse
from django.test import TestCase, Client

from users.tests import get_local_user, NORMAL
from game.tests import BaseGameDataTestCase


class TestHTMXLeaderboard(BaseGameDataTestCase):

    def test_htmx_leaderboard_resp(self):
        user = get_local_user()
        client = Client()
        client.login(email=NORMAL, password='foo')
        url = reverse('htmx-leaderboard', kwargs={'game_id': 1})
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)

