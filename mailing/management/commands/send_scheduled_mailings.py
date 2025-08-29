from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing, MailingAttempt
from django.core.mail import send_mail


class Command(BaseCommand):
    help = 'Send scheduled mailings'

    def handle(self, *args, **options):
        now = timezone.now()

        # Находим рассылки для отправки: созданные или активные, которые должны быть отправлены сейчас
        mailings = Mailing.objects.filter(
            status__in=[Mailing.STATUS_CREATED, Mailing.STATUS_STARTED],
            start_time__lte=now,
            end_time__gte=now
        )

        self.stdout.write(f"Найдено {mailings.count()} рассылок для отправки")

        for mailing in mailings:
            self.send_mailing(mailing)

    def send_mailing(self, mailing):
        """Отправка одной рассылки"""
        # Создаем запись о попытке
        attempt = MailingAttempt.objects.create(
            mailing=mailing,
            status=MailingAttempt.STATUS_SUCCESS,
            server_response='Автоматическая отправка'
        )

        successful_sends = 0
        failed_sends = 0
        last_error = None

        try:
            for client in mailing.clients.all():
                try:
                    send_mail(
                        subject=mailing.message.subject,
                        message=mailing.message.body,
                        from_email='admin@mailing-service.ru',
                        recipient_list=[client.email],
                        fail_silently=False,
                    )
                    successful_sends += 1

                except Exception as e:
                    failed_sends += 1
                    last_error = str(e)

            # Обновляем статус рассылки
            mailing.status = Mailing.STATUS_STARTED
            mailing.save()

            # Обновляем запись попытки
            if successful_sends > 0:
                attempt.server_response = f"Успешно отправлено: {successful_sends}"
                if failed_sends > 0:
                    attempt.server_response += f", Ошибок: {failed_sends}. Последняя ошибка: {last_error}"
            else:
                attempt.status = MailingAttempt.STATUS_FAILED
                attempt.server_response = f"Все отправки неудачны. Ошибка: {last_error}"

            attempt.save()

            self.stdout.write(
                f"Рассылка #{mailing.id}: {successful_sends} успешно, {failed_sends} с ошибками"
            )

        except Exception as e:
            attempt.status = MailingAttempt.STATUS_FAILED
            attempt.server_response = f"Общая ошибка: {str(e)}"
            attempt.save()
            self.stdout.write(f"Ошибка в рассылке #{mailing.id}: {str(e)}")