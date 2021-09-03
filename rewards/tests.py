from django.urls import reverse

import project.utils
from users.models import Player
from django.test import TestCase, Client
from users.tests import get_local_user, get_local_client
from game.models import Series, Answer, Question


def slackit(msg):
    print(f"Not going to slack this message: {msg}")


project.utils.slackit = slackit


class RewardTests(TestCase):
    def setUp(self):
        player = get_local_user()
        q = Question.objects.create(text='question text')
        for i in range(10):
            e = f"player{i}@localhost.com"
            p = get_local_user(e=e)
            p.referrer = player
            p.save()
            Answer.objects.create(player=p, raw_string='answer', question=q)
        self.player = player

    def test_referrer_count(self):
        self.assertEqual(self.player.players_referred.count(), 10)

    def test_claim(self):
        client = get_local_client()
        path = reverse('claim')
        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, "Please fill out this form so you can enjoy a hot drink in this beautiful mug.")

        path = reverse('claim')
        data = {'Full Name': 'NORMAL', 'Address line 1': '1 First Street', 'City': 'Patchogue',
                'State': 'NY', 'ZIP / Postal code': '12345'}
        response = client.post(path, data=data)
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, "We&#x27;ll send your prize ASAP!")

        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, "You have already claimed your mug.")
