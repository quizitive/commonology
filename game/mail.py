from django.template.loader import render_to_string
from project.utils import slackit
from mail.utils import send_one

import logging

logger = logging.getLogger(__name__)


def send_winner_notice(winner, game_number):
    slackit(f"Sending winner notification to {winner}.")
    try:
        email_context = {
            'url': f'https://commonologygame.com/award_certficate/{game_number}',
            'game_number': game_number
        }
        msg = render_to_string('game/email/winner_email.html', email_context).replace("\n", "")
        send_one(winner, 'You earned a coffee mug!', msg)
    except Exception as e:
        logger.exception(f"Could not send winner notification email {e}")
        slackit(f"{winner} won the game but something went wrong with the notification email.")
