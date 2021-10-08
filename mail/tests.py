from django.test import TestCase
from django.core import mail
from dateutil.relativedelta import relativedelta
from project.utils import our_now
from users.tests import get_local_user
from game.models import Series, Game, Question
from game.tests import BaseGameDataTestCase
from mail.utils import mass_mail, sendgrid_send
from mail.models import MailMessage, Component


class MassMailTests(BaseGameDataTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.mySetUpTestData(is_active_game=True)
        cls.game_player_not = get_local_user(e='someone@noplayer.com', subscribed=False)
        cls.mm = MailMessage.objects.create(series=cls.series,
                                            from_name='test',
                                            from_email='test@quizitive.com',
                                            test_recipient='test@quizitive.com',
                                            subject='testing_template',
                                            message='this is the mail message body')

    def test_bad_series_test(self):
        mail.outbox = []
        n = mass_mail(self.mm)
        self.assertEqual(n, 30)
        self.assertEqual(len(mail.outbox), 1)

    def test_template_component_order(self):
        mm = self.mm
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

    def test_reminder(self):
        p = self.game.players_objs[0]
        p.reminder = False
        p.save()
        mail.outbox = []
        mm = self.mm
        mm.reminder = True
        mm.save()
        n = mass_mail(self.mm)
        self.assertEqual(n, 29)
        self.assertEqual(len(mail.outbox), 1)
        p.reminder = True
        p.save()
        mm.reminder = False
        mm.save()
