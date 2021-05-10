from django.test import TestCase, Client
from django.core import mail
from users.tests import get_local_user
from game.models import Series
from mail.sendgrid_utils import mass_mail

class MassMailTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # data is written from api
        cls.series_owner = get_local_user(e='series@owner.com')
        cls.game_player = get_local_user()
        cls.game_player_not = get_local_user(e='someone@noplayer.com', subscribed=False)
        cls.series = Series.objects.create(name="Commonology", owner=cls.series_owner, public=True)
        for p in cls.series_owner, cls.game_player, cls.game_player_not:
            cls.series.players.add(p)

    def test_bad_series_test(self):
        mail.outbox = []
        n = mass_mail('test', 'hello', 'ms@quizitive.com', players=self.series.players)
        self.assertEqual(n, 2)
        self.assertEqual(len(mail.outbox), 1)


