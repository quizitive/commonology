from django.template.loader import render_to_string
from project import settings
from rewards.models import Claim
from mail.utils import send_one
from project.utils import slackit

import logging

logger = logging.getLogger(__name__)


def check_for_reward(player):
    referrer = player.referrer

    if referrer and referrer.subscribed:
        claim = Claim.objects.filter(player=referrer).first()
        if claim:
            # Don't send reward notice email if claim was already made.
            return

        if settings.REWARD_THRESHOLD == referrer.players_referred.count():
            slackit(f"{referrer} earned a coffee mug.")
            try:
                email_context = {
                    'url': f'https://commonologygame.com/claim/'
                }
                msg = render_to_string('rewards/emails/reward_earned.html', email_context).replace("\n", "")
                send_one(referrer, 'You earned a coffee mug!', msg)
            except Exception as e:
                logger.exception(f"Could not send reward notification email {e}")
                slackit(f"{referrer} earned a coffee mug but something went wrong with the notification email.")
