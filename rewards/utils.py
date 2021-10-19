import os
import subprocess
from django.template.loader import render_to_string
from project import settings
from project.utils import our_now
from mail.utils import send_one
from project.utils import slackit


import logging

logger = logging.getLogger(__name__)


def send_reward_notice(referrer):
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


def check_for_reward(player):
    if player.game_ids.count() > 1:
        # This prevents a player with 10 referees who has not claimed
        # a reward yet from getting a multiple notices when referees
        # play again.  i.e. this a new player and a new referral.
        return

    referrer = player.referrer

    if referrer:
        if settings.REWARD_THRESHOLD == referrer.players_referred.count():
            send_reward_notice(referrer)


def write_winner_certificate(name, date, game_number):
    path = settings.WINNER_ROOT
    pdf_template = "rewards/templates/rewards/WinnerCertificate.pdf"

    fn_base = f"{name}{date}{game_number}.{our_now()}".replace(',', '').replace(' ', '').strip()
    fn_base = os.path.join(path, fn_base)

    fdf = f'''
        %FDF-1.2
        1 0 obj << /FDF << /Fields [
        << /T(Name) /V({name}) >>
        << /T(Date) /V({date}) >>
        << /T(Game \#) /V({game_number}) >>
        ] >> >>
        endobj
        trailer
        << /Root 1 0 R >>
        %%EOF
    '''

    fn_fdf = fn_base + '.fdf'
    with open(fn_fdf, 'w') as fh:
        fh.write(fdf)

    fn = fn_base + '.pdf'
    p = subprocess.run(['pdftk', pdf_template, 'fill_form', fn_fdf, 'output',  fn, 'flatten'])
    print(p.returncode == 0)
    print(f'open {fn}')
