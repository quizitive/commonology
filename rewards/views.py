from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from project import settings
from project.card_views import CardFormView
from project.utils import slackit
from mail.utils import send_one
from rewards.forms import ClaimForm
from rewards.models import MailingAddress, Claim


class ClaimView(LoginRequiredMixin, CardFormView):

    form_class = ClaimForm
    card_template = "rewards/cards/claim_card.html"
    header = "Claim Reward"
    button_label = "Submit"
    custom_message_template = "rewards/components/congrats_message.html"

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
            m = (
                f"It seems you have not made {settings.REWARD_THRESHOLD} referrals yet and are not entitled to a mug."
                f" Keep going, you can do it!"
            )
            self.header = "Not eligible for claim yet."
            return self.info(
                request, message=m, form=None, form_method="get", form_action=f"/", button_label="Thank you!"
            )

        if Claim.objects.filter(player=player).exists():
            m = (
                f"We've received your claim and you will receive your mug soon. "
                f"Feel free to contact us with any questions."
            )
            self.header = "Claim staked!"
            return self.info(
                request, message=m, form=None, form_method="get", form_action=f"/contact/", button_label="Contact us"
            )

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

        claim_msg = render_to_string("rewards/emails/reward_claimed.html", {"address": address}).replace("\n", "")
        send_one(player, "Order confirmation", claim_msg)

        self.custom_message = mark_safe(
            f"Thanks! We'll send your prize ASAP. " f"We've sent a confirmation email to <b>{player.email}.</b>"
        )
        self.header = "Claim staked!"
        return self.render(request, form=None, form_method="get", form_action=f"/", button_label="Thank you!")
