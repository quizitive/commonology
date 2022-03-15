import datetime
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import login
from project.utils import our_now
from users.models import Player, PendingEmail


class PlayerBackend(ModelBackend):

    def authenticate(self, request, **kwargs):
        if request is not None:
            user_id = kwargs.get('user_id')
            if user_id is None:
                user_id = request.session.get('user_id')
            else:
                request.session['user_id'] = user_id

            try:
                return Player.objects.get(id=user_id)
            except Player.DoesNotExist:
                pass


class PlayerActivateError(Exception):
    pass


# Reference: https://stackoverflow.com/questions/2787650/manually-logging-in-a-user-without-password
def activate_account(request, uuid):
    pe = PendingEmail.objects.filter(uuid__exact=uuid).first()
    if pe is None:
        raise PlayerActivateError('Seems like there was a problem with the validation link. Please try again.')

    if pe.created < (our_now() - datetime.timedelta(minutes=20)):
        raise PlayerActivateError('The validation link sent to you is more than 20 minutes old.')

    email = pe.email
    try:
        p = Player.objects.get(email=email)
    except Player.DoesNotExist:
        p = Player(email=email, referrer=pe.referrer)
        p.save()

    if not p.is_active:
        p.activate()
        p.save()

    login(request, p, backend='django.contrib.auth.backends.ModelBackend')
    pe.delete()

    return p
