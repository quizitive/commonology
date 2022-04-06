from django.core.management.base import BaseCommand
from users.utils import merge_players


class Command(BaseCommand):
    help = 'Merge Players.'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs='+', type=str, help="<from_email> <into_email>")

    def handle(self, *args, **kwargs):
        from_email, to_email = kwargs['email']
        merge_players(from_email, to_email)
