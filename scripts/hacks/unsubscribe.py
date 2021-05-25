from mail.sendgrid_utils import suppressions
from django.contrib.auth import get_user_model
import csv

reasons = ['unrecognized address',
           'The email account that you tried to reach is over quota.',
           'user lookup success but no user record found',
           'connect: no route to host',
           'i/o timeout',
           'no such user']



response = suppressions()

for i in response.body:

    print(i['email'], i['reason'])
exit()

fn = 'suppression_blocks.csv'
with open(fn) as csvfile:
    reader = csv.reader(csvfile)
    data = [row for row in reader]

#data.sort(key=lambda x:x[1])
unsubscribe_members = [i[2] for i in data if any(r in i[1] for r in reasons)]
for i in unsubscribe_members:
    print(i)

exit()
unsubscribed_members = unsubscribed_members.split()

User = get_user_model()

qs = User.objects.filter(email__in=unsubscribed_members).all()
for u in qs:
    if u.subscribed:
        print(f"unsubscribing {u.email}")
        u.subscribed = False
        u.save()
