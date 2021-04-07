import os
import pandas as pd

from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from project.utils import REDIS
from leaderboard.leaderboard import build_filtered_leaderboard, build_answer_tally, lb_cache_key
from game.models import Game, AnswerCode
from game.tests import BaseGameDataTestCase
from users.models import Team
from django.contrib.auth import get_user_model

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


class TestLeaderboardViews(BaseGameDataTestCase):

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


class TestLeaderboardEngine(BaseGameDataTestCase):

    def setUp(self):
        super().setUp()

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
        User = get_user_model()
        expected_leaderboard['id'] = expected_leaderboard.apply(
            lambda x: User.objects.get(display_name=x['Name']).id,
            axis=1
        ).astype('int64')
        expected_leaderboard['is_host'] = expected_leaderboard.apply(
            lambda x: x['id'] in self.game.hosts.values_list('id', flat=True),
            axis=1
        )
        q_list = [q.text for q in self.questions[:10]]
        expected_leaderboard = expected_leaderboard[['id', 'is_host', 'Rank', 'Name', 'Score'] + q_list]
        return expected_leaderboard.reset_index(drop=True)

    def test_host_exclusion(self):

        player = self._add_host()

        # test that the admin is excluded from game answer tally (28 answers per question v 29)
        at_excl_hosts = build_answer_tally(self.game)
        self.assertTrue(all([sum([r for r in resp.values()]) == 28 for resp in at_excl_hosts.values()]))

        # --------------- DEPRECATED --------------------- #
        # - Host results can be shown for now, but not a part of score - #

        # and excluded from the leaderboard
        # leaderboard = build_filtered_leaderboard(self.game, at_excl_hosts)
        # self.assertEqual(sum(leaderboard["Name"] == "User 1"), 0)
        # ------------------------------------------------- #

        # unless it's a team view
        team = Team.objects.create()
        team.players.add(player)
        leaderboard = build_filtered_leaderboard(self.game, at_excl_hosts, team_id=team.id)
        self.assertEqual(sum(leaderboard["Name"] == "User 1"), 1)

    def test_omitted_unique_answer(self):
        # test that if an omitted answer (e.g. a host or something offensive) is a unique string
        # leaderboard can still be rendered
        player = self._add_host()

        # change an answer to something unique
        unique_string = 'foo-999-xxx-unique'
        an_answer = player.answers.first()
        an_answer.raw_string = unique_string
        an_answer.save()

        # give the answer a unique coding
        AnswerCode.objects.create(
            raw_string=unique_string,
            question=an_answer.question,
            coded_answer=unique_string
        )

        # recreate the answer tally and leaderboard
        new_answer_tally = build_answer_tally(self.game)
        REDIS.delete(lb_cache_key(self.game, new_answer_tally))
        new_leaderboard = build_filtered_leaderboard(self.game, new_answer_tally)

        # make sure they get 0 points
        self.assertEqual(
            new_leaderboard.loc[new_leaderboard['Name'] == player.display_name,
                                an_answer.question.text].values[0], 0)

    def _add_host(self, email="user1@fakeemail.com"):
        # make user a game host
        User = get_user_model()
        player = User.objects.get(email=email)
        self.game.hosts.add(player)
        self.game.save()
        return player
