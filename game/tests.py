import os
from os import environ as env
from time import sleep
import re
import datetime
import dateutil
import string
import random
import json
import logging
from urllib.parse import quote_plus
from copy import deepcopy
from csv import reader
from dateutil.relativedelta import relativedelta

from django.utils.timezone import make_aware
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.db import IntegrityError
from django.core.files.storage import FileSystemStorage

import game.gsheets_api
from project.celery import stubbed_task
# Rather than provide gdrive credentials to ci tests we'll just stub with no-op.
# Do this before gsheets_api is imported elsewhere
game.gsheets_api.write_new_responses_to_gdrive = stubbed_task

from project.utils import our_now, redis_delete_patterns, REDIS
from leaderboard.leaderboard import build_filtered_leaderboard, build_answer_tally, lb_cache_key, winners_of_game
from leaderboard.tasks import save_last_visit_t
from users.tests import get_local_user, get_local_client, ABINORMAL
from users.models import Player, PendingEmail
from game.utils import next_wed_noon, next_friday_1159, write_winner_certificate, n_new_comments
from game.models import Game, Series, Question, Answer
from game.views import PSIDMixin, find_latest_public_game
from game.rollups import *
from game.tasks import questions_to_db, players_to_db, answers_codes_to_db, answers_to_db

from game.forms import QuestionAnswerForm
from users.tests import test_pw
from chat.models import Comment

from django.contrib.auth import get_user_model


LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


def suppress_hidden_error_logs(func):
    """
    PermissionDenied, Http404, SystemExit and Suspicious operation errors
    are not visible because they're handled by Django internally.
    This decorator prevents writing to logs that clog up test output
    See https://docs.djangoproject.com/en/dev/topics/testing/tools/#exceptions
    """
    def wrapper(*args, **kwargs):
        logging.disable(logging.CRITICAL)
        func(*args, **kwargs)
        logging.disable(logging.NOTSET)
    return wrapper


class HomePage(TestCase):

    def test_page(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


class BaseGameDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Need this so that derived classes can add to setup test data
        cls.mySetUpTestData()

    @classmethod
    def mySetUpTestData(cls):
        cls.resp_fp = f'{LOCAL_DIR}/test_data/test_data.csv'
        cls.rollup_fp = f'{LOCAL_DIR}/test_data/test_rollups.csv'
        cls.sheet_name = "Test Commonology Game (Responses)"
        with open(cls.resp_fp, 'r') as f:
            raw = reader(f)
            raw_responses = list(raw)
            cls.resp_df = api_data_to_df(raw_responses)
        with open(cls.rollup_fp, 'r') as f:
            raw = reader(f)
            raw_rollups = list(raw)
            cls.rollups = build_rollups_dict(raw_rollups)

        # data is written from api
        cls.series_owner = get_local_user(e='series@owner.com')
        cls.game_player = get_local_user()
        cls.series = Series.objects.create(name="Commonology", owner=cls.series_owner, public=True)

        t = our_now()
        cls.game = Game.objects.create(series=cls.series, name="Test Commonology Game", start=t, end=t)
        cls.questions = questions_to_db(cls.game, cls.resp_df)

        players_to_db(cls.series, cls.resp_df)
        answers_to_db(cls.game, cls.resp_df)
        cls.answer_codes = build_answer_codes(cls.resp_df, cls.rollups)
        answers_codes_to_db(cls.game, cls.answer_codes)

        # calculation methods
        cls.answer_tally = build_answer_tally(cls.game)
        cls.leaderboard = build_filtered_leaderboard(cls.game, cls.answer_tally)
        cls.leaderboard_obj = cls.game.leaderboard

    @classmethod
    def tearDownClass(cls):
        REDIS.delete(lb_cache_key(cls.game, cls.answer_tally))
        super().tearDownClass()

    def activate_game(self):
        t = our_now()
        self.game.start = t
        self.game.end = t + relativedelta(hours=1)
        self.game.save()

    @classmethod
    def deactivate_game(cls):
        cls.game.end = cls.game.start


class TestGameTabulation(BaseGameDataTestCase):

    def test_raw_data_to_df(self):
        # make a raw data df
        raw_data_df = pd.read_csv(self.resp_fp)

        # test no duplicate emails
        dupe_emails_raw = raw_data_df[raw_data_df.duplicated('Email Address', keep=False)]
        self.assertEqual(len(dupe_emails_raw), 2)
        dupe_emails_clean = self.resp_df[self.resp_df.duplicated('Email Address')]
        self.assertEqual(len(dupe_emails_clean), 0)

        # test email remaining is the first one
        first_resp_ts = min(dupe_emails_raw['Timestamp'])
        dupe_email = dupe_emails_raw['Email Address'].iloc[0]
        kept_resp_ts = self.resp_df[self.resp_df['Email Address'] == dupe_email]['Timestamp'].iloc[0]
        self.assertEqual(first_resp_ts, kept_resp_ts)

    def test_close_enough(self):
        # test a simple spelling case
        self.assertTrue(close_enough('pretzel', 'pretxel', {}))

        # test short strings don't count
        self.assertFalse(close_enough('foo', 'fob', {}))

        # test a number string
        self.assertTrue(close_enough('4', 'four', {}))

    def test_build_rollups_dict(self):
        # make sure it's still a list of dicts for all questions
        expected_qs = list(self.resp_df.iloc[:, 3:-2].columns)
        rollup_qs = list(self.rollups.keys())
        self.assertEqual(expected_qs, rollup_qs)

    def test_default_rollups(self):
        # make sure we've assigned some value to non-reviewed rollups
        missing_rollups = deepcopy(self.rollups)
        missing_rollups[list(self.rollups.keys())[1]] = {}
        mr_answer_tally = build_answer_tally(self.game)
        self.assertEqual(mr_answer_tally, self.answer_tally)

        # this won't work if any answers don't have an associated code
        build_filtered_leaderboard(self.game, mr_answer_tally)

    # DEPERECATED!! We don't do this anymore
    # def test_game_to_db(self):
    #     self.assertEqual(self.game.sheet_name, self.sheet_name)
    #     self.assertEqual(self.game.name, "Test Commonology Game")
    #
    #     # test new game of same name is not created on save
    #     game = self.game
    #     game2 = game_to_db(self.series, self.sheet_name, start=game.start, end=game.end)
    #     self.assertEqual(self.game, game2)

    def test_game_id_increments(self):
        t = our_now()
        e = t + relativedelta(hours=1)
        game2 = Game.objects.create(series=self.series, start=t, end=e)
        self.assertEqual(game2.game_id, 2)

    def test_questions_to_db(self):
        self.assertEqual(len(self.questions), 12)

    def test_players_to_db(self):
        players = self.game.players_dict
        self.assertEqual(len(players), 29)

        new_disply_name_df = pd.DataFrame(
            columns=['Email Address', 'Name'],
            data=[['user1@fakeemail.com', 'New Display Name']]
        )
        players_to_db(self.series, new_disply_name_df)
        User = get_user_model()
        new_display_name = User.objects.get(email='user1@fakeemail.com').display_name
        self.assertEqual(new_display_name, 'New Display Name')

    def test_player_name_trim(self):
        long_name = ''.join(random.choices(string.ascii_letters, k=199))
        new_disply_name_df = pd.DataFrame(
            columns=['Email Address', 'Name'],
            data=[['long_name@fakeemail.com', long_name]]
        )
        players_to_db(self.series, new_disply_name_df)
        User = get_user_model()
        new_display_name = User.objects.get(email='long_name@fakeemail.com').display_name
        self.assertEqual(new_display_name, long_name[:100])

    def test_answers_to_db(self):
        # test answers to game questions
        answers = Answer.objects.exclude(question__type=Question.op)
        self.assertEqual(answers.count(), 290)

        # test running again doesn't add new records
        answers_to_db(self.game, self.resp_df)
        self.assertEqual(answers.count(), 290)

    def test_blank_answers(self):
        new_user_email = "userx@fakeemail.com"
        User = get_user_model()
        p = User.objects.create(email=new_user_email)
        new_answer_with_blanks = pd.DataFrame([[
            "2020-12-02 16:11:00",
            new_user_email,
            "UserX",
            "",
            "Big",
            'D. "Sourdough / Large"',
            "Winbledon",
            "PEE-can",
            "",
            "Ontario",
            "The Amazing Race",
            "Katie",
            "Pancakes",
            "",
            ""
        ]], columns=self.resp_df.columns)
        resp_df = self.resp_df.append(new_answer_with_blanks)
        answers_to_db(self.game, resp_df)

        # test we still save blanks for required (game) questions
        blank_answer = Answer.objects.get(question__text=resp_df.columns[3], player=p)
        self.assertEqual(blank_answer.raw_string, "")

        # test we don't save blanks for optional questions
        self.assertEqual(Answer.objects.filter(question__type=Question.op, player=p).count(), 0)

    def test_answer_codes(self):
        # test coded answers (one for each unique string)
        answer_code_objs = AnswerCode.objects.all()
        self.assertEqual(answer_code_objs.count(), 104)

        # test codes are updated if they're changed
        a_question = Question.objects.get(text="Excluding Forest Gump, name a Tom Hanks movie.")
        answer_codes = deepcopy(self.answer_codes)
        answers = answer_codes[a_question.text]

        # move an answers string from one code to another and reprocess
        orig_code = list(answers)[0]
        new_code = list(answers)[1]
        raw_string = answers[orig_code].pop()
        answers[new_code].append(raw_string)
        answers_codes_to_db(self.game, answer_codes)

        # test it is updated
        a_changed_code = AnswerCode.objects.get(question=a_question, raw_string=raw_string)
        self.assertEqual(a_changed_code.coded_answer, new_code)

        # change it back
        answers_codes_to_db(self.game, self.answer_codes)


class TestGSheetsAPI(BaseGameDataTestCase):

    def setUp(self):
        self.rollups_and_tallies = build_rollups_and_tallies(self.answer_tally, self.answer_codes)

    def test_make_answers_sheet(self):
        with open(f'{LOCAL_DIR}/test_data/test_answers.json', 'r') as f:
            expected_answers_sheet = json.load(f)
        answers_sheet = make_answers_sheet(self.rollups_and_tallies)
        self.assertEqual(answers_sheet, expected_answers_sheet)

    def test_make_merges_sheet(self):
        with open(f'{LOCAL_DIR}/test_data/test_rollups.json', 'r') as f:
            expected_rollups_sheet = json.load(f)
        rollups_sheet = make_rollups_sheet(self.rollups_and_tallies)
        self.assertEqual(rollups_sheet, expected_rollups_sheet)


class TestUtils(TestCase):

    def test_next_wed_noon(self):
        a_tuesday = make_aware(datetime.datetime(year=2021, month=2, day=1))
        next_game_start = next_wed_noon(a_tuesday)
        self.assertEqual(next_game_start.weekday(), 2)
        self.assertEqual(next_game_start.hour, 12)

    def test_next_fri_1159(self):
        a_thursday = make_aware(datetime.datetime(year=2021, month=2, day=3))
        next_game_end = next_friday_1159(a_thursday)
        self.assertEqual(next_game_end.weekday(), 4)
        self.assertEqual(next_game_end.strftime(format="%H:%M:%S"), "23:59:59")

    def test_clear_redis_trailing_wildcard(self):
        key1 = 'leaderboard_3_@crAzyS+r!ng'
        key2 = 'leaderboard_3_$0H!pSoHODL'
        REDIS.set(key1, "a value")
        REDIS.set(key2, "a value")
        redis_delete_patterns(['leaderboard_3'])
        self.assertIsNone(REDIS.get(key1))
        self.assertIsNone(REDIS.get(key2))


class TestModels(TestCase):

    def test_series(self):
        user = get_local_user()
        series = Series.objects.create(name="Series 1", owner=user)

        # test slugify on save
        self.assertEqual(series.slug, "series-1")

        # test owner is host and player
        self.assertIn(user, series.hosts.all())
        self.assertIn(user, series.players.all())

    def test_game_host_is_series_player(self):
        series, game = make_test_series()
        user = get_local_user()
        game.hosts.add(user)
        self.assertIn(user, series.players.all())

    def test_optional_questions(self):
        op_q = Question.objects.create(
            text="This question is optional.", type=Question.op, number=1, choices=['a', 'b'])
        self.assertEqual(op_q.text, "OPTIONAL: This question is optional.")

        user = get_local_user()
        op_q_form = QuestionAnswerForm(op_q, data={
            'question': op_q,
            'raw_string': '',
            'player': user
        })

        self.assertNotIn("required", op_q_form.as_p())
        self.assertTrue(op_q_form.is_valid())

    def test_unique_question_number(self):
        series, game = make_test_series()
        with self.assertRaises(IntegrityError):
            Question.objects.create(game=game, text='q1', number=1)


def make_test_series(series_name='Commonology', hour_window=False):
    series_owner = get_local_user(e='series@owner.com')
    series = Series.objects.create(name=series_name, owner=series_owner, public=True)
    t = et = our_now()
    if hour_window:
        et = t + relativedelta(hours=1)
    game = Game.objects.create(series=series, name="Test Commonology Game", start=t, end=et)
    game.save()
    question = Question.objects.create(text="Are you my mother?", number=1)
    game.questions.add(question)
    return series, game


class TestPlayRequest(TestCase):
    def setUp(self):
        self.series, self.game = make_test_series(series_name='Commonology', hour_window=True)
        pub_date = self.game.end + relativedelta(days=1)
        self.leaderboard = self.game.leaderboard
        self.player = get_local_user()

    def test_find_latest_public_game(self):
        slug = 'commonology'
        game = find_latest_public_game(slug)
        self.assertIsNotNone(game)

        self.game.end = self.game.start
        self.game.save()

        game = find_latest_public_game(slug)
        self.assertIsNone(game)

    def test_no_games(self):
        client = Client()
        path = '/c/foobar/play/'
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cannot find an active game.  Join so we can let you know when the next game begins.')

    def test_with_google_form(self):
        # test with uuid and without
        g = self.game
        g.google_form_url = 'https://docs.google.com/forms/u/1/d/1nrL3Me1hek9loJqNHWnCkphfLZhKP4D1C_92pYbK3sU/'
        g.save()

        client = Client()
        path = '/play/'
        response = client.get(path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, g.google_form_url)

        path = reverse('game:uuidplay', kwargs={'game_uuid': g.uuid})
        response = client.get(path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, g.google_form_url)

    def test_game_host(self):
        game = self.game
        game.end = game.start
        game.save()

        client = get_local_client()
        path = f'/play/{game.uuid}/'
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seems like the game finished but has not been scored yet.')

        self.series.hosts.add(self.player)
        path = f'/play/{game.uuid}/'
        response = client.get(path)
        self.assertContains(response, self.game.questions.first().text)

        # This should fail because find latest game would return None and so no game can be found.
        path = f'/play/'
        response = client.get(path)
        self.assertContains(response, 'Cannot find an active game.  We will let you know when the next game begins.')

    def test_with_login(self):
        game = self.game
        client = get_local_client()

        path = '/play/'
        response = client.get(path)
        self.assertContains(response, game.questions.first().text)

        path = reverse('game:uuidplay', kwargs={'game_uuid': game.uuid})
        response = client.get(path)
        self.assertContains(response, game.questions.first().text)

        game.end = game.start
        game.save()
        path = '/play/'
        response = client.get(path)
        self.assertContains(response, 'Cannot find an active game.  We will let you know when the next game begins.')

        path = reverse('game:uuidplay', kwargs={'game_uuid': game.uuid})
        response = client.get(path)
        self.assertContains(response, 'Seems like the game finished but has not been scored yet.')

        self.leaderboard.publish_date = our_now()
        self.leaderboard.save()
        path = reverse('game:uuidplay', kwargs={'game_uuid': game.uuid})
        response = client.get(path)
        self.assertContains(response, 'Seems like the game finished.  See the leaderboard.')

    def get_invite_url(self, email):
        client = Client()
        mail.outbox = []
        response = client.post(reverse('game:play'), data={"email": email})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "forget to check your spam or junk folder if need be.")
        msg = mail.outbox[0].body
        url = re.search("(?P<url>https?://[^\s]+)\"\>Click", msg).group("url")
        mail.outbox = []
        return url

    def test_without_login(self):
        # try with just /play and /c/rambus/play and /c/commonology/play
        # test with uuid and without
        game = self.game
        path = reverse('game:uuidplay', kwargs={'game_uuid': game.uuid})

        client = Client()
        response = client.get(path)
        self.assertEqual(response.status_code, 200)

        p = Player.objects.filter(email=ABINORMAL).first()
        self.assertIsNone(p)
        self.assertContains(response, "Enter your email address to play.")

        url = self.get_invite_url(email=ABINORMAL)
        pe = PendingEmail.objects.filter(email=ABINORMAL).first()
        self.assertIsNotNone(pe)

        response = client.get(url)
        self.assertContains(response, game.questions.first().text)

        # Was player created
        p = Player.objects.filter(email=ABINORMAL).first()
        self.assertIsNotNone(p)

        # delete pe record and test for failure
        Player.objects.filter(email=ABINORMAL).delete()
        PendingEmail.objects.all().delete()
        response = client.get(url)
        self.assertContains(response, 'Seems like there was a problem with the validation link. Please try again.')

    def test_stale_email_confirm_link(self):
        game = self.game
        client = Client()

        url = self.get_invite_url(email=ABINORMAL)
        pe = PendingEmail.objects.filter(email=ABINORMAL).first()
        self.assertIsNotNone(pe)
        game.end = game.start
        game.save()
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sorry the next game is no longer active.')

    def test_bad_uuid(self):
        game = self.game

        uuid = str(game.uuid)
        last_char = uuid[-1]
        if last_char == '0':
            last_char = '1'
        else:
            last_char = '0'
        uuid = uuid[:-1] + last_char

        path = reverse('game:uuidplay', kwargs={'game_uuid': uuid})
        client = Client()
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cannot find an active game.  Perhaps you have a bad link.')

        client = get_local_client()
        path = reverse('game:uuidplay', kwargs={'game_uuid': uuid})
        client = Client()
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cannot find an active game.  Perhaps you have a bad link.')

    def test_game_reviewer(self):
        # Game url with uuid should render the game without a submit button prior to game start.
        game = self.game

        client = get_local_client()
        path = f'/play/{game.uuid}/'
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.game.questions.first().text)
        self.assertNotContains(response, "Thanks for playing!")

        # Make sure the game has not started yet to test preview mode.
        game.start = game.end
        game.save()

        client = get_local_client()
        path = f'/play/{game.uuid}/'
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.game.questions.first().text)
        # Since the game is in preview mode, not editable then it has the Thank you string.
        self.assertContains(response, "Thanks for playing!")

    def test_submit_button_id(self):
        client = get_local_client()
        path = f'/play/{self.game.uuid}/'
        response = client.get(path)

        self.assertContains(response, '<button id="submit-button"')


class TestViews(TestCase):

    def test_suggest_question(self):
        # anonymous user redirects to login
        client = Client()
        response = client.get(reverse('game:question-suggest'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/?next=/suggest-a-question/')

        # logged in user renders form
        get_local_user()
        client = get_local_client()
        response = client.get(reverse('game:question-suggest'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Suggest a Question")

        # post form sends email
        mail.outbox = []
        client.post(
            reverse('game:question-suggest'),
            data={"suggestion": "A question suggestion"}
        )
        self.assertEqual(len(mail.outbox), 1)


class TestGameForm(BaseGameDataTestCase, PSIDMixin):

    def setUp(self):
        self.player = get_local_user()
        self.client = get_local_client()
        self.game_form_url = reverse('series-game:game-form',
                                     kwargs={'series_slug': self.series.slug, 'game_id': self.game.game_id})
        self.psid = self.sign_game_player(self.game, self.player)

    def test_game_form_view(self):
        # can't render game form directly (needs to go through GameValidationView)
        response = self.client.get(self.game_form_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/play/{self.game.uuid}/')

    def test_game_form_post_success(self):
        form_data = self._valid_game_form_data()
        self._test_game_form_post_response(form_data, 'Your answers have been submitted.')

    def test_incomplete_form_post_fail(self):
        form_data = self._psid_display_name_form_data()
        # bad game data redirects to game form
        self._test_game_form_post_response(form_data, self.game.questions.first().text)

    def test_valid_string_not_in_choices(self):
        # if an answer isn't in choices, redirect to game form
        q = self.game.questions.first()
        q.choices = ['foo', 'bar']
        q.save()
        form_data = self._valid_game_form_data()
        self._test_game_form_post_response(form_data, self.game.questions.first().text)
        self._test_game_form_post_response(form_data, 'div class="errors"')

    def _psid_display_name_form_data(self) -> list:
        return [
            (('psid', self.psid),),
            (('display_name', 'test_guy'),)
        ]

    def _valid_game_form_data(self) -> list:
        form_data = self._psid_display_name_form_data()
        form_data.extend([
            (('question', str(q.id)), ('raw_string', f'test_{q.id}')) for q in self.game.questions.all()
        ])
        return form_data

    def _url_encode_form_data(self, form_data):
        # accepts a list of tuples (representing a form) which contains key value pair tuples representing
        # field name and value e.g. ('form_field', 'value') and outputs as encoded form data
        url_encoded = f'?'
        for form in form_data:
            url_encoded += '&' + '&'.join([f'{k}={quote_plus(v)}' for k, v in form])
        return url_encoded

    def _test_game_form_post_response(self, game_data, expected_text):
        response = self.client.post(
            self.game_form_url,
            data=self._url_encode_form_data(game_data),
            content_type="application/x-www-form-urlencoded"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_text)


class CertificateTests(BaseGameDataTestCase):
    def remove_winner_files(self, fn):
        if env.get('GITHUB_COMMONOLOGY_CI_TEST'):
            return

        fs = FileSystemStorage(location=settings.WINNER_ROOT)
        fs.delete(fn)
        fn = fn.removesuffix('.pdf') + '.fdf'
        fs.delete(fn)

    def test_write(self):
        fn = write_winner_certificate(name='Marc Schwarzschild', date='October 21, 2021', game_number=59)
        self.assertEqual(fn, 'MarcSchwarzschildOctober21202159.pdf')
        self.remove_winner_files(fn)

    def test_award_certificate(self):
        player = winners_of_game(self.game)[0]
        player.set_password('foobar')
        player.save()

        client = get_local_client(player.email, pw='foobar')
        path = reverse('game:award_certificate', kwargs={'game_id': self.game.game_id})
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        headers = response.headers
        self.assertEqual(headers['Content-Type'], 'application/pdf')
        if 'Content-Disposition' in headers:
            fn = headers['Content-Disposition'].replace('attachment; filename=', '')
            self.remove_winner_files(fn)

        player.set_password('')
        player.save()


class SessionReferralTests(BaseGameDataTestCase):
    # In these tests the referral code was introduced to the session as an argument on the home page.

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game.end = our_now() + relativedelta(hours=1)
        cls.game.save()

    def start_session(self, name='home'):
        self.user1 = get_local_user()
        client = Client()
        path = reverse(name) + f'?r={self.user1.code}'
        client.get(path)
        self.assertEqual(self.user1.code, client.session.get('r'))
        return client

    def url_tester(self, name='home'):
        client = self.start_session(name)
        mail.outbox = []
        email = 'button_player@commonologygame.com'
        response = client.post(reverse('game:play'), data={"email": email})
        self.assertEqual(response.status_code, 200)

        pe = PendingEmail.objects.filter(email=email).first()
        self.assertEqual(pe.referrer, self.user1)

        msg = mail.outbox[0].body
        url = re.search("(?P<url>https?://[^\s]+)\"\>Click", msg).group("url")
        mail.outbox = []

        pe.delete()

    def test_play_from_home(self):
        self.url_tester('home')

    def test_play_from_referral_rules(self):
        self.url_tester('raffle_rules')

    def test_play_from_play(self):
        # Special case: click play link but don't submit. Leave page.  Then use play link on sise somewhere.
        client = self.start_session('game:play')
        response = client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

        email = 'button_player@commonologygame.com'
        response = client.post(reverse('game:play'), data={"email": email})
        self.assertEqual(response.status_code, 200)

        pe = PendingEmail.objects.filter(email=email).first()
        self.assertEqual(pe.referrer, self.user1)

    def test_join(self):
        client = self.start_session()
        email = 'button_player@commonologygame.com'

        mail.outbox = []
        response = client.post(reverse('join'), data={"email": email})
        self.assertEqual(response.reason_phrase, 'OK')

        pe = PendingEmail.objects.filter(email=email).first()
        self.assertEqual(pe.referrer, self.user1)


class NewMessageIndicatorTests(BaseGameDataTestCase):
    # In these tests the referral code was introduced to the session as an argument on the home page.
    def setUp(self):
        self.leaderboard_obj.publish_date = our_now() - datetime.timedelta(days=1)
        self.leaderboard_obj.save()
        self.authenticated_client = Client(raise_request_exception=False)
        self.authenticated_client.login(email=self.game_player.email, password=test_pw)
        self.question = self.game.game_questions.first()

    def add_comment(self, player, s, t):
        thread = self.question.thread
        c = Comment(player=player, created=t, comment=s, thread=thread)
        c.save()

    def get_time(self, client, player):
        # Set session time
        response = client.get(reverse('leaderboard:current-results'))
        self.assertEqual(response.status_code, 200)
        player = Player.objects.get(id=player.id)
        last_visit_t = player.data.get(f'results_last_visit_t:{self.series.slug}:{self.game.game_id}')
        last_visit_t = dateutil.parser.isoparse(last_visit_t)
        return last_visit_t

    def test_indicator(self):
        client1 = self.authenticated_client
        player1 = self.game_player
        player2 = get_local_user(e='two@foo.com')
        client2 = get_local_client(e='two@foo.com')
        player3 = get_local_user(e='three@foo.com')
        client3 = get_local_client(e='three@foo.com')
        comment_badge = "<div id=\"comment-indicator-badge-container\">"

        # Set session time for client 1 and client2
        self.get_time(client2, player2)
        last_visit_t = self.get_time(client1, player1)
        last_visit_plus_5 = last_visit_t + datetime.timedelta(minutes=5)

        # There are no comments yet
        f = n_new_comments(self.game, player1, last_visit_t)
        self.assertFalse(f)

        # Player 2 adds a comment 6 minutes after player 1 last visited the results page.
        self.add_comment(player2, 'hi', last_visit_t + datetime.timedelta(minutes=6))
        flag = n_new_comments(self.game, player1, last_visit_plus_5)
        self.assertTrue(flag)

        # Player 1 visits the leaderboard which indicates a new message.
        response = client1.get(reverse('leaderboard:current-leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, comment_badge)

        # Player 2 visits the leaderboard but should not see an indication because he posted new comment
        response = client2.get(reverse('leaderboard:current-leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, comment_badge)

        # Player 3 visits leaderboard but never visited results
        response = client3.get(reverse('leaderboard:current-leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, comment_badge)

    def test_save_last_visit_t(self):
        player_id = self.game_player.id
        t = our_now().isoformat()
        key = 'leaderboard_last_t'
        save_last_visit_t.delay(player_id, key, t)
        sleep(10)
        p = Player.objects.get(id=player_id)
        self.assertEqual(p.data[key], t)
