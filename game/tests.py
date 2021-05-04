import datetime
import string
import random
import json
from copy import deepcopy
from csv import reader

from django.test import TestCase, Client
from django.urls import reverse

from project.utils import REDIS
from leaderboard.leaderboard import build_filtered_leaderboard, build_answer_tally, lb_cache_key
from users.tests import get_local_user
from game.utils import next_wed_noon, next_friday_1159
from game.models import Series, Question, Answer
from game.rollups import *
from game.gsheets_api import *
from game.tasks import game_to_db, questions_to_db, players_to_db, \
    answers_codes_to_db, answers_to_db

from django.contrib.auth import get_user_model


LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


class HomePage(TestCase):

    def test_page(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


class BaseGameDataTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.resp_fp = f'{LOCAL_DIR}/test_data/test_data.csv'
        cls.rollup_fp = f'{LOCAL_DIR}/test_data/test_rollups.csv'
        cls.sheet_name = "Test FF Game (Responses)"
        with open(cls.resp_fp, 'r') as f:
            raw = reader(f)
            raw_responses = list(raw)
            cls.resp_df = api_data_to_df(raw_responses)
        with open(cls.rollup_fp, 'r') as f:
            raw = reader(f)
            raw_rollups = list(raw)
            cls.rollups = build_rollups_dict(raw_rollups)

        # data is written from api
        cls.game = game_to_db(cls.sheet_name)
        cls.questions = questions_to_db(cls.game, cls.resp_df)
        players_to_db(cls.resp_df)
        answers_to_db(cls.game, cls.resp_df)
        cls.answer_codes = build_answer_codes(cls.resp_df, cls.rollups)
        answers_codes_to_db(cls.game, cls.answer_codes)

        # calculation methods
        cls.answer_tally = build_answer_tally(cls.game)
        cls.leaderboard = build_filtered_leaderboard(cls.game, cls.answer_tally)

    @classmethod
    def tearDownClass(cls):
        REDIS.delete(lb_cache_key(cls.game, cls.answer_tally))
        super().tearDownClass()


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

    def test_game_to_db(self):
        self.assertEqual(self.game.sheet_name, self.sheet_name)
        self.assertEqual(self.game.name, "Test FF Game")

        # test new game of same name is not created on save
        game2 = game_to_db(self.sheet_name)
        self.assertEqual(self.game, game2)

    def test_game_id_increments(self):
        game2 = game_to_db('game2')
        self.assertEqual(game2.game_id, 2)

    def test_questions_to_db(self):
        self.assertEqual(len(self.questions), 12)

    def test_players_to_db(self):
        players = self.game.players
        self.assertEqual(len(players), 29)

        new_disply_name_df = pd.DataFrame(
            columns=['Email Address', 'Name'],
            data=[['user1@fakeemail.com', 'New Display Name']]
        )
        players_to_db(new_disply_name_df)
        User = get_user_model()
        new_display_name = User.objects.get(email='user1@fakeemail.com').display_name
        self.assertEqual(new_display_name, 'New Display Name')

    def test_player_name_trim(self):
        long_name = ''.join(random.choices(string.ascii_letters, k=199))
        new_disply_name_df = pd.DataFrame(
            columns=['Email Address', 'Name'],
            data=[['long_name@fakeemail.com', long_name]]
        )
        players_to_db(new_disply_name_df)
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
        self.assertEqual(answer_code_objs.count(), 70)

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
        a_tuesday = datetime.datetime(year=2021, month=2, day=1)
        next_game_start = next_wed_noon(a_tuesday)
        self.assertEqual(next_game_start.weekday(), 2)
        self.assertEqual(next_game_start.hour, 12)

    def test_next_fri_1159(self):
        a_thursday = datetime.datetime(year=2021, month=2, day=3)
        next_game_end = next_friday_1159(a_thursday)
        self.assertEqual(next_game_end.weekday(), 4)
        self.assertEqual(next_game_end.strftime(format="%H:%M:%S"), "23:59:59")


class TestModels(TestCase):

    def test_series(self):
        user = get_local_user()
        series = Series.objects.create(name="Series 1", owner=user)

        # test slugify on save
        self.assertEqual(series.slug, "series-1")

        # test owner is host and player
        self.assertIn(user, series.hosts.all())
        self.assertIn(user, series.players.all())
