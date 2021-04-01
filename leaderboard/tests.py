import os
import pandas as pd

from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from game.models import Game
from game.tests import BaseGameDataTestCase

from users.models import Player

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


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

    def test_build_answer_tally(self):
        canada_answer_tally = {
            k: v for k, v in self.answer_tally["Name a province in Canada."].items()
            if v
        }
        self._test_answer_tally(canada_answer_tally)

    def _test_answer_tally(self, answer_tally):
        correct_tally = pd.Series(
            data=[13, 10, 3, 1, 1, 1],
            index=["Quebec", "Ontario", "British Columbia", "Ottowa", "Nova Scotia", "New Brunswick"]
        )
        # Test the labels
        self.assertSetEqual(set(correct_tally.keys()), set(answer_tally.keys()))

        for idx in correct_tally.index:
            self.assertEqual(correct_tally[idx], answer_tally[idx])

    def test_build_leaderboard(self):
        expected_leaderboard = self._expected_leaderboard()
        expected_leaderboard.rename(columns={"Name (First & Last)": "Name"}, inplace=True)
        pd.testing.assert_frame_equal(
            expected_leaderboard, self.leaderboard.reset_index(drop=True)
        )

    def _expected_leaderboard(self):
        # local test data file plus some computed/related values
        lb_data_fp = f'{LOCAL_DIR}/test_data/test_leaderboard.csv'
        expected_leaderboard = pd.read_csv(lb_data_fp, index_col=0)
        expected_leaderboard['Rank'] = expected_leaderboard['Rank'].astype('int32')
        expected_leaderboard['Score'] = expected_leaderboard['Score'].astype('int32')
        expected_leaderboard['id'] = expected_leaderboard.apply(
            lambda x: Player.objects.get(display_name=x['Name']).id,
            axis=1
        ).astype('int64')
        expected_leaderboard['is_host'] = expected_leaderboard.apply(
            lambda x: x['id'] in self.game.hosts.values_list('id', flat=True),
            axis=1
        )
        q_list = [q.text for q in self.questions[:10]]
        expected_leaderboard = expected_leaderboard[['id', 'is_host', 'Rank', 'Name', 'Score'] + q_list]
        return expected_leaderboard.reset_index(drop=True)
