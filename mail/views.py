import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import send_mail
from project.views import CardFormView
from mail.forms import OneMailForm
from mail.utils import sendgrid_send


@login_required
@permission_required("is_superuser")
def mailtest(request):
    emailaddr = request.user.email
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Mail sent to {emailaddr} at {now}."

    send_mail(subject="Sending test.", message=message, from_email=None, recipient_list=[emailaddr])

    return render(request, "mail/mailtest.html", {"message": message, "emailaddr": emailaddr})


class OneMailView(UserPassesTestMixin, CardFormView):

    def test_func(self):
        return self.request.user.is_staff

    form_class = OneMailForm
    header = "One Mail Form"
    button_label = "Submit"

    def post(self, request, *args, **kwargs):
        self.custom_message = ""
        form = self.get_form()

        if form.is_valid():
            data = form.data

            email = data["email"]
            from_email = data["from_email"]
            subject = data["subject"]
            message = data["message"]

            self.custom_message = "Message sent."
            try:
                sendgrid_send(subject, message, from_email=from_email, email_list=[(email, "UNKNOWN")])
            except IOError:
                self.custom_message = f"For some reason we could not make the award certificate."

            return redirect("mail:one_mail")

        return self.render(request)
