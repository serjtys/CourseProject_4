from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing, MailingAttempt
from django.core.mail import send_mail


class Command(BaseCommand):
    help = 'Send scheduled mailings'

    def handle(self, *args, **options):
        now = timezone.now()

        # Находим рассылки для отправки
        mailings = Mailing.objects.filter(
            status__in=[Mailing.STATUS_CREATED, Mailing.STATUS_STARTED],
            start_time__lte=now,
            end_time__gte=now
        )

        for mailing in mailings:
            self.send_mailing(mailing)

    def send_mailing(self, mailing):
        try:
            for client in mailing.clients.all():
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email='noreply@mailing-service.ru',
                    recipient_list=[client.email],
                    fail_silently=False,
                )

                # Создаем запись об успешной попытке
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response='Успешно отправлено'
                )

            mailing.status = Mailing.STATUS_STARTED
            mailing.save()

        except Exception as e:
            # Создаем запись о неудачной попытке
            MailingAttempt.objects.create(
                mailing=mailing,
                status=MailingAttempt.STATUS_FAILED,
                server_response=str(e)
            )