from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from project.card_views import CardFormView
from rewards.forms import ClaimForm


class ClaimView(LoginRequiredMixin, CardFormView):

    form_class = ClaimForm
    page_template = 'rewards/cards/claim_page.html'
    header = "Claim Reward"
    button_label = 'Submit'

    def get(self, request, *args, **kwargs):
        messages.info(request, "Please fill out this form so you can enjoy a hot drink in this beautiful mug.")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        form = self.get_form()

        if not form.is_valid():
            messages.error(request, "There was a problem saving your changes. Please try again.")
            return self.render(request)

        address = form.save(commit=False)
        address.player = request.user
        form.save()

        m = "We'll send your prize ASAP!"

        self.header = "Claim staked!"
        return self.info(request,
                         message=m,
                         form=None,
                         form_method='get')
