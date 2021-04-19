
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import To

from users.utils import sign_user


def make_substitutions(e, i):
    x = sign_user(e, i)
    url = mark_safe(f"https://{settings.DOMAIN}/unsubscribe/{x}")
    return {'-email-': e, '-unsubscribelink-': url}


def sendgrid_send(subject, msg, email_list,
                  from_email=(settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL_NAME)):

    to_emails = [To(email=e, substitutions=make_substitutions(e, id)) for e, id in email_list]

    msg = render_to_string('mail/massmail.html', context={'message': mark_safe(msg)})

    message = Mail(
        from_email=from_email,
        subject=subject,
        to_emails=to_emails,
        plain_text_content='Game is on.',
        html_content=msg,
        is_multiple=True)
    try:
        sendgrid_client = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)

        response = sendgrid_client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
