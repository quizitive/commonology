from django.template.loader import render_to_string
from project import settings
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

def replace_text(content, replacements = dict()):
    lines = content.splitlines()

    result = ""
    in_text = False

    for line in lines:
        if line == "BT":
            in_text = True

        elif line == "ET":
            in_text = False

        elif in_text:
            cmd = line[-2:]
            if cmd.lower() == 'tj':
                replaced_line = line
                for k, v in replacements.items():
                    replaced_line = replaced_line.replace(k, v)
                result += replaced_line + "\n"
            else:
                result += line + "\n"
            continue

        result += line + "\n"

    return result


def process_data(object, replacements):
    data = object.getData()
    decoded_data = data.decode('utf-8')
    # decoded_data = data.decode("utf-8", "ignore")

    replaced_data = replace_text(decoded_data, replacements)

    encoded_data = replaced_data.encode('utf-8')
    if object.decodedSelf is not None:
        object.decodedSelf.setData(encoded_data)
    else:
        object.setData(encoded_data)


def write_certificate():
    # https://stackoverflow.com/questions/17742042/how-to-fill-pdf-form-in-python
    # https://stackoverflow.com/questions/41769120/search-and-replace-for-text-within-a-pdf-in-python

    from io import BytesIO
    import PyPDF2
    from PyPDF2.generic import BooleanObject, NameObject, IndirectObject, NumberObject

    replacements = {'Joshua Louis Simon': 'Marc Schwarzschild'}

    pdf_template = "project/static/img/WinnerCertificate.pdf"
    input_stream = open(pdf_template, "rb")
    pdf_reader = PyPDF2.PdfFileReader(ippnput_stream, strict=False)
    pdf_writer = PyPDF2.PdfFileWriter()

    page = pdf_reader.getPage(0)
    # content = page.extractText()
    contents = page.getContents()
    process_data(contents, replacements)

    page[NameObject("/Contents")] = contents.decodedSelf

    pdf_writer.addPage(page)


    with open("marc.pdf", 'wb') as out_file:
        pdf_writer.write(out_file)
