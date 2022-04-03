import os
import pandas as pd

from django.urls import reverse
from django.test import Client

from project.utils import REDIS, our_now, redis_delete_patterns
from leaderboard.leaderboard import build_filtered_leaderboard, lb_cache_key, winners_of_game, build_leaderboard_fromdb
from leaderboard.models import PlayerRankScore
from game.models import Game, Answer
from game.tests import BaseGameDataTestCase, suppress_hidden_error_logs

from users.models import Player
from users.tests import test_pw
from leaderboard.templatetags.leadeboard_tags import formatted_answer_cell

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


class TestLeaderboardViews(BaseGameDataTestCase):

    def setUp(self):
        self.leaderboard_obj.publish_date = our_now()
        self.leaderboard_obj.save()
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

    def test_htmx_leaderboard_resp(self):
        game_id = max(Game.objects.values_list('game_id'))[0]

        # most recent game is public
        url = reverse('leaderboard:htmx')
        pub_resp = self.client.get(url, {'game_id': game_id, 'series': self.series.slug})
        self.assertEqual(pub_resp.status_code, 200)

        # non-staff can't see unpublished games, redirect to login
        new_game = Game.objects.create(series=self.series, start=our_now(), end=our_now())
        resp = self.client.get(url, {'game_id': new_game.game_id, 'series': self.series.slug})
        self.assertEqual(resp.status_code, 302)

        # staff users can access games if they exist
        self.client.login(email=self.su_email, password='foo')
        staff_resp = self.client.get(url, {'game_id': new_game.game_id, 'series': self.series.slug})
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
        player = Player.objects.get(email='user1@fakeemail.com')
        player_answers = self.game.leaderboard.qid_answer_dict(player.id)

        # this is just to mock the for loop in the template
        resvals = [{'res': res, 'val': val} for res, val in self.answer_tally[self.questions[0].text].items()]
        context = {
            'answer_tally': self.answer_tally,
            'player_answers': player_answers,
            'game_top_commentary': self.leaderboard_obj.top_commentary,
            'game_bottom_commentary': self.leaderboard_obj.bottom_commentary,
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
        self.assertTrue({'game_id': self.game.game_id,
                         'game_name': self.game.name,
                         'series': self.game.series.slug} in player.game_ids)
        # there is a leaderboard cached for the game
        self.assertIsNotNone(REDIS.keys(f'leaderboard_{self.game.series.slug}_{self.game.game_id}*'))

        # posting a new display name empties the cache
        data = {'display_name': 'new_display_name'}
        client.post(path, data=data)
        self.assertEqual(REDIS.keys(f'leaderboard_{self.game.series.slug}_{self.game.game_id}'), [])

    def test_winners_of_game(self):
        expected_winner_email = 'user7@fakeemail.com'
        winner = winners_of_game(self.game).first()
        self.assertEqual(winner.email, expected_winner_email)

    def test_removed_answers_arent_counted(self):
        player = Player.objects.get(email='user1@fakeemail.com')
        Answer.objects.filter(player=player).update(removed=True)
        redis_delete_patterns('*')
        leaderboard = build_filtered_leaderboard(self.game, self.answer_tally)
        self.assertEqual(len(leaderboard), len(self.leaderboard) - 1)

    def test_save_player_rank_scores(self):
        player = Player.objects.get(email='user1@fakeemail.com')
        player_prs_qs = PlayerRankScore.objects.filter(player=player)
        self.assertTrue(player_prs_qs.exists())

        player_prs = player_prs_qs.first()
        original_value = player_prs.score
        player_prs.score = 0
        player_prs.save()
        self.assertNotEqual(player_prs.score, original_value)

        build_leaderboard_fromdb(self.game, self.answer_tally)
        new_value = PlayerRankScore.objects.filter(player=player).first().score
        self.assertEqual(original_value, new_value)
