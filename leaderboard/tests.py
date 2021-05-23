import os
import pandas as pd

from django.urls import reverse
from django.test import Client

from project.utils import REDIS, our_now
from leaderboard.leaderboard import build_filtered_leaderboard, lb_cache_key
from game.models import Game
from game.tests import BaseGameDataTestCase, suppress_hidden_error_logs

from users.models import Player
from users.tests import test_pw
from leaderboard.templatetags.leadeboard_tags import formatted_answer_cell

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


class TestLeaderboardViews(BaseGameDataTestCase):

    def setUp(self):
        self.game.publish = True
        self.game.save()
        self.client = Client()
        self.su_email = "super@user.com"
        self.admin_user = Player.objects.create_superuser(self.su_email, 'foo')
        self.authenticated_client = Client(raise_request_exception=False)
        self.authenticated_client.login(email=self.game_player.email, password=test_pw)

    def _assert_code(self, url, code):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code)

    def test_leaderboard_view(self):
        url = reverse('leaderboard:current-leaderboard')
        self._assert_code(url, 200)

    @suppress_hidden_error_logs
    def test_leaderboard_game_view(self):
        # non-staff user can't see other weeks directly
        url = reverse('leaderboard:game-id-leaderboard', kwargs={'game_id': 1})
        self._assert_code(url, 404)

    def test_htmx_leaderboard_resp(self):
        game_id = max(Game.objects.values_list('game_id'))[0]

        # most recent game is public
        url = reverse('leaderboard:htmx')
        pub_resp = self.client.get(url, {'game_id': game_id})
        self.assertEqual(pub_resp.status_code, 200)

        # non-staff can't see unpublished games, redirect to login
        new_game = Game.objects.create(publish=False, series=self.series, start=our_now(), end=our_now())
        resp = self.client.get(url, {'game_id': new_game.game_id})
        self.assertEqual(resp.status_code, 302)

        # staff users can access games if they exist
        self.client.login(email=self.su_email, password='foo')
        staff_resp = self.client.get(url, {'game_id': new_game.game_id})
        self.assertEqual(staff_resp.status_code, 200)
        self.assertNotEqual(staff_resp.content, pub_resp.content)

    # ---- removed from urls.py until finished ---- #
    # def test_player_home(self):
    #     url = reverse('leaderboard:player-home')
    #     resp = self.authenticated_client.get(url)
    #     self.assertEqual(resp.status_code, 200)

    @suppress_hidden_error_logs
    def test_series_permissions_leaderboard(self):
        # make the series private
        self.series.public = False
        self.series.save()
        url = reverse('series-leaderboard:current-leaderboard', kwargs={'series_slug': self.series.slug})
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (403, 302))

        # a logged in user that is not a player of the series cannot view
        resp = self.authenticated_client.get(url)
        self.assertEqual(resp.status_code, 403)

        # but if they're a player, they can view
        self.series.players.add(self.game_player)
        resp = self.authenticated_client.get(url)
        self.assertEqual(resp.status_code, 200)

    # ---- Template Tag Tests ---- #
    def test_formatted_answer_cell(self):
        player_answers = self.game.coded_player_answers.filter(player__email='user1@fakeemail.com')

        # this is just to mock the for loop in the template
        resvals = [{'res': res, 'val': val} for res, val in self.answer_tally[self.questions[0].text].items()]
        context = {
            'answer_tally': self.answer_tally,
            'player_answers': player_answers,
            'game_top_commentary': self.game.top_commentary,
            'game_bottom_commentary': self.game.bottom_commentary,
            'questions': self.questions,
            'host': self.game.hosts.first(),
            'q': self.questions[0],
        }

        # make sure we're evaluating player-answer class correctly
        context.update(resvals[0])
        player_answer = formatted_answer_cell(context, 1)
        self.assertIn('player-answer', player_answer)

        # make sure player-answer is not on a non-answer
        context.update(resvals[1])
        not_player_answer = formatted_answer_cell(context, 1)
        self.assertNotIn('player-answer', not_player_answer)

        # make sure we're hiding the long tail
        hidden_after_ten = formatted_answer_cell(context, 11)
        self.assertIn('style="display:none;"', hidden_after_ten)


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

    # --------------- DEPRECATED --------------------- #
    # - Host results are no longer excluded fro score - #

    # def test_host_exclusion(self):
    #
    #     player = self._add_host()
    #
    #     # test that the admin is excluded from game answer tally (28 answers per question v 29)
    #     at_excl_hosts = build_answer_tally(self.game)
    #     self.assertTrue(all([sum([r for r in resp.values()]) == 28 for resp in at_excl_hosts.values()]))
    #
    #     # and excluded from the leaderboard
    #     # leaderboard = build_filtered_leaderboard(self.game, at_excl_hosts)
    #     # self.assertEqual(sum(leaderboard["Name"] == "User 1"), 0)
    #
    #     # unless it's a team view
    #     team = Team.objects.create()
    #     team.players.add(player)
    #     leaderboard = build_filtered_leaderboard(self.game, at_excl_hosts, team_id=team.id)
    #     self.assertEqual(sum(leaderboard["Name"] == "User 1"), 1)

    # ------------------------------------------------- #

    # --------------- DEPRECATED --------------------- #
    # the only way of "omitting" a player at this point is to make them
    # a host, but per the above note, this functionality has been deprecated.
    # when there is a way of omitting an answer by any other means, make sure
    # this test passes
    # def test_omitted_unique_answer(self):
    #     # test that if an omitted answer (e.g. a host or something offensive) is a unique string
    #     # leaderboard can still be rendered
    #     player = self._add_host()
    #
    #     # change an answer to something unique
    #     unique_string = 'foo-999-xxx-unique'
    #     an_answer = player.answers.first()
    #     an_answer.raw_string = unique_string
    #     an_answer.save()
    #
    #     # give the answer a unique coding
    #     AnswerCode.objects.create(
    #         raw_string=unique_string,
    #         question=an_answer.question,
    #         coded_answer=unique_string
    #     )
    #
    #     # recreate the answer tally and leaderboard
    #     new_answer_tally = build_answer_tally(self.game)
    #     REDIS.delete(lb_cache_key(self.game, new_answer_tally))
    #     new_leaderboard = build_filtered_leaderboard(self.game, new_answer_tally)
    #
    #     # make sure they get 0 points
    #     self.assertEqual(
    #         new_leaderboard.loc[new_leaderboard['Name'] == player.display_name,
    #                             an_answer.question.text].values[0], 0)
    # ------------------------------------------------- #

    def _add_host(self, email="user1@fakeemail.com"):
        # make user a game host
        player = Player.objects.get(email=email)
        self.game.hosts.add(player)
        self.game.save()
        return player

    def test_leaderboard_search(self):
        # basic leaderboard search
        filtered_leaderboard = build_filtered_leaderboard(self.game, self.answer_tally, search_term="5")
        self.assertEqual(len(filtered_leaderboard), 3)
        REDIS.delete(lb_cache_key(self.game, self.answer_tally))

        # make sure regex is escaped, search for literals
        user5 = Player.objects.get(display_name="User 5")
        user5.display_name = "*5*"
        user5.save()
        re_filtered_leaderboard = build_filtered_leaderboard(self.game, self.answer_tally, search_term="*5*")
        self.assertEqual(len(re_filtered_leaderboard), 1)

    def test_display_name_clears_cache(self):
        player = Player.objects.get(display_name="User 5")
        user5_pass = 'iamuser5'
        player.password = user5_pass
        player.save()
        client = Client()
        client.login(email=player.email, password=user5_pass)
        path = reverse('profile')

        # the player has played self.game
        self.assertTrue({'game_id': self.game.game_id, 'series': self.game.series.slug} in player.game_ids)
        # there is a leaderboard cached for the game
        self.assertIsNotNone(REDIS.keys(f'leaderboard_{self.game.series.slug}_{self.game.game_id}*'))

        # posting a new display name empties the cache
        data = {'display_name': 'new_display_name'}
        client.post(path, data=data)
        self.assertEqual(REDIS.keys(f'leaderboard_{self.game.series.slug}_{self.game.game_id}'), [])
