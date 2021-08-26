from django.test import TestCase, Client
from django.core import mail
from users.tests import get_local_user
from game.models import Series
from mail.sendgrid_utils import mass_mail, sendgrid_send
from mail.models import MailMessage, Component


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

    def test_template_component_order(self):
        mm = MailMessage.objects.create(
            series=self.series,
            from_name='test',
            from_email='test@quizitive.com',
            test_recipient='test@quizitive.com',
            subject='testing_template',
            message='this is the mail message body'
        )
        c1 = Component.objects.create(
            name='component1',
            template='mail/simple_component.html',
            message='<b>bolded string</b>',
            context={'name': 'component_1'}
        )
        c2 = Component.objects.create(
            name='component2',
            template='mail/simple_component.html',
            message='<i>italic string</i>',
            context={'name': 'component_2'}
        )
        mm.components.add(c2, c1)
        _, rendered_msg = sendgrid_send(
            subject=mm.subject,
            msg=mm.message,
            email_list=[],
            from_email=mm.from_email,
            components=mm.components.all()
        )

        c1_loc = rendered_msg.find('<b>bolded string</b>')
        c2_loc = rendered_msg.find('<i>italic string</i>')

        # assert the components are in the rendered message
        self.assertNotEqual(c1_loc, -1)
        self.assertNotEqual(c2_loc, -1)

        # assert c2 comes before c1
        self.assertLess(c2_loc, c1_loc)

        # move c1 to top, make sure it's above message
        c1.location = Component.top
        c1.save()
        _, rendered_msg = sendgrid_send(
            subject=mm.subject,
            msg=mm.message,
            email_list=[],
            from_email=mm.from_email,
            components=mm.components.all()
        )
        msg_loc = rendered_msg.find('this is the mail message body')
        c1_new_loc = rendered_msg.find('<b>bolded string</b>')
        self.assertLess(c1_new_loc, msg_loc)
