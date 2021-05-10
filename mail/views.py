import datetime
from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from users.utils import unsubscribe, subscribe


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
