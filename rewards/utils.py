from django.template.loader import render_to_string
from project import settings
from mail.utils import send_one
from mail.tasks import send_refer_thankyou
from project.utils import slackit


import logging

logger = logging.getLogger(__name__)


def send_reward_notice(referrer):
    slackit(f"{referrer} earned a coffee mug.")
    try:
        email_context = {"url": f"https://commonologygame.com/claim/"}
        msg = render_to_string("rewards/emails/reward_earned.html", email_context).replace("\n", "")
        send_one(referrer, "You earned a coffee mug!", msg)
    except Exception as e:
        logger.exception(f"Could not send reward notification email {e}")
        slackit(f"{referrer} earned a coffee mug but something went wrong with the notification email.")


def check_for_reward(player):
    if player.game_ids.count() > 1:
        # This prevents a player with 10 referees who has not claimed
        # a reward yet from getting a multiple notices when referees
        # play again.  i.e. this a new player and a new referral.
        return

    referrer = player.referrer

    if referrer:
        send_refer_thankyou(player)
        if settings.REWARD_THRESHOLD == referrer.players_referred.count():
            send_reward_notice(referrer)
