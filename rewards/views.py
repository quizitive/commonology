from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from project.card_views import CardFormView
from rewards.forms import ClaimForm
from rewards.models import MailingAddress, Claim


class ClaimView(LoginRequiredMixin, CardFormView):

    form_class = ClaimForm
    page_template = 'rewards/cards/claim_page.html'
    header = "Claim Reward"
    button_label = 'Submit'

    def get_form(self, form_class=None):
        player = self.request.user
        try:
            a = MailingAddress.objects.get(player=player)
        except MailingAddress.DoesNotExist:
            a = None
        form = self.form_class(instance=a, data=self.request.POST or None)
        return self.format_form(form)

    def get(self, request, *args, **kwargs):
        player = request.user
        if Claim.objects.filter(player=player).exists():
            m = "You have already claimed your mug.  Sorry, but we are limited one per customer."
            self.header = "Claim staked!"
            return self.info(request,
                             message=m,
                             form=None,
                             form_method='get',
                             form_action=f'/',
                             button_label='Thank you!')

        messages.info(request, "Please fill out this form so you can enjoy a hot drink in this beautiful mug.")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        form = self.get_form()

        if not form.is_valid():
            messages.error(request, "There was a problem saving your changes. Please try again.")
            return self.render(request)

        player = request.user

        address = form.save(commit=False)
        address.player = player
        form.save()

        c = Claim(player=player)
        c.save()

        m = "We'll send your prize ASAP!"

        self.header = "Claim staked!"
        return self.info(request,
                         message=m,
                         form=None,
                         form_method='get',
                         form_action=f'/',
                         button_label='Thank you!')
