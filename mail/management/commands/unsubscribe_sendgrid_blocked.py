from django.core.management.base import BaseCommand
from mail.utils import deactivate_blocked_addresses


class Command(BaseCommand):
    help = 'Unsubscribe addresses blocked at sendgrid and remove them from the blocked list.'

    def handle(self, *args, **options):
        deactivate_blocked_addresses()
        print('This should have unsubscribed blocked and spam reported addresss.')
        print('Visit sendgrid and clear those suppression lists.')
