import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail


@login_required
@permission_required('is_superuser')
def mailtest(request):
    emailaddr = request.user.email
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Mail sent to {emailaddr} at {now}."

    send_mail(subject="Sending test.", message=message,
              from_email=None, recipient_list=[emailaddr])

    return render(request, 'mail/mailtest.html',
                  {'message': message, "emailaddr": emailaddr})
