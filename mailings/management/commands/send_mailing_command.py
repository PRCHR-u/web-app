from django.core.management.base import BaseCommand, CommandError
from mailings.models import Mailing
from mailings.tasks import send_mailing_task

class Command(BaseCommand):
    help = 'Sends a specific mailing by its ID'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='The ID of the mailing to send')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']

        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            raise CommandError(f'Mailing with ID "{mailing_id}" does not exist')

        self.stdout.write(self.style.SUCCESS(f'Triggering send for mailing ID {mailing_id}...'))
        send_mailing_task.delay(mailing_id)
        self.stdout.write(self.style.SUCCESS('Mailing task queued successfully.'))