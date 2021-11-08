from django.db import transaction


def un_sub(modeladmin, request, qs, subscribed):
    with transaction.atomic():
        for u in qs:
            u.subscribed = subscribed
            u.save()


def unsubscribe_action(modeladmin, request, qs):
    un_sub(modeladmin, request, qs, False)


unsubscribe_action.description = "Unsubscribe"


def subscribe_action(modeladmin, request, qs):
    un_sub(modeladmin, request, qs, True)


subscribe_action.description = "Subscribe"
