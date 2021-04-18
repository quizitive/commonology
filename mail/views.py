import datetime
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .forms import MassEmailForm
from .models import MassMailMessage
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


@method_decorator(csrf_exempt, name='dispatch')
class MailchimpWebhook(View):

    def get(self, request, uuid=None):
        # Need this for Mailchimp to validate hook when setting up an audience.
        return HttpResponse("OK")

    def post(self, request, uuid):
        assert(uuid == settings.MAILCHIMP_HOOK_UUID)

        data = request.POST
        list_id = data['data[list_id]']
        assert(list_id == str(settings.MAILCHIMP_EMAIL_LIST_ID))

        email = data['data[email]']
        action = data.get('type', 'unknown')
        if action == 'unsubscribe':
            unsubscribe(email)
        elif action == 'subscribe':
            subscribe(email)
        elif action == 'archived':
            unsubscribe(email)

        return HttpResponse("OK")


class MassMail(PermissionRequiredMixin, View):
    permission_required = 'is_staff'

    def get(self, request):
        m = MassMailMessage.objects.first()
        form = MassEmailForm(m)
        return render(request, 'mail/massmaileditor.html', {'form': form})

    def post(self, request):
        form = MassEmailForm(request.POST)
        if form.is_valid():
            pass
        else:
            pass
        return redirect('/')
