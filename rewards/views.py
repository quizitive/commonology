from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from project import settings
from project.card_views import CardFormView
from project.utils import slackit
from rewards.forms import ClaimForm
from rewards.models import MailingAddress, Claim


class ClaimView(LoginRequiredMixin, CardFormView):

    form_class = ClaimForm
    # page_template = 'cards/base_card.html'
    card_template = 'rewards/cards/claim_card.html'
    header = "Claim Reward"
    button_label = 'Submit'
    custom_message_template = 'rewards/components/congrats_message.html'

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
        can_claim = player.players_referred.count() >= settings.REWARD_THRESHOLD
        if not can_claim:
            self.congrat_message = ""
            m = f"It seems you have not made {settings.REWARD_THRESHOLD} referrals yet and are not entitled to a mug." \
                f" Keep going, you can do it!"
            self.header = "Not eligible for claim yet."
            return self.info(request, message=m, form=None, form_method='get',
                             form_action=f'/', button_label='Thank you!')

        if Claim.objects.filter(player=player).exists():
            self.congrat_message = ""
            m = "You have already claimed your mug.  Sorry, but we are limited one per customer."
            self.header = "Claim staked!"
            return self.info(request, message=m, form=None, form_method='get',
                             form_action=f'/', button_label='Thank you!')

        return super().get(request, can_claim=can_claim, *args, **kwargs)

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

        slack_msg = f"{player} just claimed a coffee mug."
        slackit(slack_msg)

        m = "We'll send your prize ASAP!"
        self.header = "Claim staked!"
        return self.info(request,
                         message=m,
                         form=None,
                         form_method='get',
                         form_action=f'/',
                         button_label='Thank you!')
