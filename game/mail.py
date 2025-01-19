import posixpath
from django.template.loader import render_to_string
from project.utils import slackit
from project.settings import DOMAIN, WINNER_ROOT
from mail.utils import send_one

import logging

logger = logging.getLogger(__name__)


def send_winner_notice(winner, game_number):
    slackit(f"Sending winner notification to {winner}.")
    try:
        email_context = {
            "url": f"https://commonologygame.com/award_certificate/{game_number}",
            "game_number": game_number,
        }
        msg = render_to_string("game/email/winner_email.html", email_context).replace("\n", "")
        send_one(winner, "You are a winner in this weeks game!", msg)
    except Exception as e:
        logger.exception(f"Could not send winner notification email {e}")
        slackit(f"{winner} won the game but something went wrong with the notification email.")


def send_prior_winner_notice(winner, game_number, filename):
    slackit(f"Sending winner notification to {winner} for game {game_number}.")

    url = posixpath.join(f"https://{DOMAIN}", WINNER_ROOT, filename)
    try:
        email_context = {"url": url, "game_number": game_number}
        msg = render_to_string("game/email/winner_email_prior.html", email_context).replace("\n", "")
        send_one(winner, "Award Certificate", msg)
    except Exception as e:
        logger.exception(f"Could not send winner notification email {e}")
        slackit(f"{winner} won game {game_number} but something went wrong with the notification email.")
