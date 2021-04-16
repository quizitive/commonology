
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import To


def try_it():
    message = '''
    
Hi everyone!

Happy Wednesday and welcome to a new week of Friendship Feud. Last week we had 1,166 players from all over the country and the world!* As always, the points reset and this week could be YOUR week to win!

Below is a link to a new survey. Remember: the goal is to guess the most common answer, not necessarily YOUR answer. Please spread the word and invite others to play, just don't discuss your answers until after you have each submitted! The rest of the rules are on the survey itself. 

You have until 11:59 PM EST on Friday, April 9 to get your answers in. I'll send out the results on Monday. Good luck!

<p><A HREF="https://commonologygame.com">Let's Play Friendship Feud!</a></p>

Alex

*Last week, I included a question about where players live to give you all a better idea of who you're up against. In case you missed the results of that question, here they are: 

No response: 245
Maryland: 129
New York: 124
California: 70
DC: 70
Illinois: 61
Colorado: 46
Virginia: 44
Texas: 40
New Jersey: 38
Massachusetts: 33
Connecticut: 32
Florida: 30
Ohio: 25
Pennsylvania: 25
North Carolina: 18
Ontario: 13
Tennessee: 13
Indiana: 12
Minnesota: 10 
Michigan: 8
Missouri: 8
Washington: 8
South Carolina: 7
Georgia: 6
Wisconsin: 6
Rhode Island: 5
Arizona: 3
Kansas: 3
Montana: 3
Alabama: 2
Delaware: 2
Idaho: 2
Kentucky: 2
Utah: 2
Vermont: 2
Alaska: 1
British Columbia: 1
Iowa: 1
Louisiana: 1
Oklahoma: 1
Oregon: 1
Quebec: 1

France: 2
Hungary: 2
Belgium: 1
Fiji: 1
Ireland: 1
South Africa: 1
United Kingdom: 1

Still trying to get players in: Arkansas, Hawaii, Maine, Mississippi, Nebraska, Nevada, New Hampshire, New Mexico, North Dakota, South Dakota, West Virginia, Wyoming - so if you know anyone who lives in these states, spread the word!
'''
    context = {'message': mark_safe(message), 'uuid': '-uuid-'}
    msg = render_to_string('mail/newgame.html', context)

    email_list = [('ms@koplon.com', 'Marc', 'MarcUUID'),
                  ('popsalooloo@yahoo.com', 'pops', 'PopsUUID')]

    subject = 'Commonology Game - New Survey!'

    sendgrid_send(subject, msg, email_list, from_email=('alex@commonologygame.com', 'Alex Fruin'))


def sendgrid_send(subject, msg, email_list,
                  from_email=(settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL_NAME)):

    to_emails = [To(email=e, name=n, substitutions={'-name-': n, '-email-': e, '-uuid-': u})
                 for e, n, u in email_list]

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
