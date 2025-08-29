from django.db import models

class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    body = models.TextField(verbose_name='Тело письма')
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Владелец')

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        permissions = [
            ('can_view_all_messages', 'Может просматривать все сообщения'),
        ]

class Client(models.Model):
    email = models.EmailField(unique=True, verbose_name='Email')
    full_name = models.CharField(max_length=255, verbose_name='Ф. И. О.')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Владелец')

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        permissions = [
            ('can_view_all_clients', 'Может просматривать всех клиентов'),
        ]


class Mailing(models.Model):
    STATUS_CREATED = 'created'
    STATUS_STARTED = 'started'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    start_time = models.DateTimeField(verbose_name='Дата и время первой отправки')
    end_time = models.DateTimeField(verbose_name='Дата и времени окончания отправки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name='Статус')
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Владелец')

    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name='Сообщение')

    clients = models.ManyToManyField(Client, verbose_name='Получатели')

    def __str__(self):
        return f"Рассылка #{self.id} ({self.status}) от {self.start_time}"

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        permissions = [
            ('can_view_all_mailings', 'Может просматривать все рассылки'),
            ('can_disable_mailings', 'Может отключать рассылки'),
        ]


class MailingAttempt(models.Model):
    # Статусы попытки
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время попытки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Статус попытки')
    server_response = models.TextField(blank=True, null=True, verbose_name='Ответ почтового сервера')

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, verbose_name='Рассылка')
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Владелец')  # Добавляем

    def save(self, *args, **kwargs):
        """Автоматически проставляем владельца из рассылки"""
        if self.mailing and self.mailing.owner:
            self.owner = self.mailing.owner
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Попытка {self.mailing_id} - {self.status}"

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылки'
