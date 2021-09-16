from project import settings
from users.models import Player
from mail.utils import send_one
from project.utils import slackit

import logging

logger = logging.getLogger(__name__)


def check_for_reward(player):
    if player.referrer:
        if settings.REWARD_THRESHOLD == player.referrer.players_referred.count():
            slackit(f"{player} earned a coffee mug.")
            try:
                send_one(player, 'You earned a coffee mug.!',
                         f'Thank you for referring {settings.REWARD_THRESHOLD} players to Commonology. '
                         f'Use this link to claim your reward: https://commonologygame.com/claim')
            except Exception as e:
                logger.exception(f"Could not send reward notification email {e}")
                slackit(f"{player} earned a coffee mug but something went wrong with the notification email.")
