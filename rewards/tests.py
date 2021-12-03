from django.urls import reverse
from django.core import mail

import project.utils
from project import settings
from django.test import TestCase
from users.tests import get_local_user, get_local_client
from game.models import Answer, Question
from rewards.utils import check_for_reward


def slackit(msg):
    print(f"Not going to slack this message: {msg}")


project.utils.slackit = slackit
project.settings.REWARD_THRESHOLD = 3


class RewardTests(TestCase):
    def setUp(self):
        self.player = get_local_user()
        self.q = Question.objects.create(text='question text')
        for i in range(settings.REWARD_THRESHOLD - 1):
            self.make_referee(i)

    def make_referee(self, i):
        e = f"player{i}@localhost.com"
        p = get_local_user(e=e)
        p.referrer = self.player
        p.save()
        Answer.objects.create(player=p, raw_string='answer', question=self.q)
        return p

    def test_claim(self):
        client = get_local_client()
        path = reverse('claim')

        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, f"It seems you have not made {settings.REWARD_THRESHOLD} referrals yet")

        p = self.make_referee(settings.REWARD_THRESHOLD)

        mail.outbox = []
        check_for_reward(p)
        self.assertEqual(mail.outbox[1].subject, 'You earned a coffee mug!')
        self.assertEqual(mail.outbox[0].subject, "Thank you for the referral.")

        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, "Please fill out this form so you can enjoy a hot drink in your beautiful new mug.")

        data = {'name': 'NORMAL', 'address1': '1 First Street', 'city': 'Patchogue',
                'state': 'NY', 'zip_code': '12345'}
        response = client.post(path, data=data)
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, "sent a confirmation email to")

        response = client.get(path)
        self.assertEqual(response.reason_phrase, 'OK')
        self.assertContains(response, "Claim staked!")
