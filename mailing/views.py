from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Client, Message, Mailing, MailingAttempt
from django import forms
from django.core.mail import send_mail
from django.contrib import messages
from django.views.decorators.cache import cache_page
from .mixins import OwnerRequiredMixin
from django.db.models import Count, Q, F
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def index(request):
    total_mailings = Mailing.objects.count()
    active_mailings = Mailing.objects.filter(status='started').count()
    unique_clients = Client.objects.distinct().count()

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_clients': unique_clients,
    }
    return render(request, 'mailing/index.html', context)

class ClientListView(ListView):
    model = Client
    template_name = 'mailing/client_list.html'

    def get_queryset(self):
        """Показываем все объекты админам, а обычным пользователям - только свои"""
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        elif self.request.user.is_authenticated:
            return queryset.filter(owner=self.request.user)
        return queryset.none()

class ClientCreateView(CreateView):
    model = Client
    fields = ('email', 'full_name', 'comment')
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('mailing:client_list')

    def form_valid(self, form):
        """Автоматически проставляем владельца при создании"""
        if self.request.user.is_authenticated:
            form.instance.owner = self.request.user
        return super().form_valid(form)

class ClientUpdateView(OwnerRequiredMixin, UpdateView):
    model = Client
    fields = ('email', 'full_name', 'comment')
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('mailing:client_list')

class ClientDeleteView(OwnerRequiredMixin, DeleteView):
    model = Client
    template_name = 'mailing/client_confirm_delete.html'
    success_url = reverse_lazy('mailing:client_list')

class MessageListView(ListView):
    model = Message
    template_name = 'mailing/message_list.html'

    def get_queryset(self):
        """Показываем все объекты админам, а обычным пользователям - только свои"""
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        elif self.request.user.is_authenticated:
            return queryset.filter(owner=self.request.user)
        return queryset.none()

class MessageCreateView(CreateView):
    model = Message
    fields = ('subject', 'body')
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        """Автоматически проставляем владельца при создании"""
        if self.request.user.is_authenticated:
            form.instance.owner = self.request.user
        return super().form_valid(form)

class MessageUpdateView(OwnerRequiredMixin, UpdateView):
    model = Message
    fields = ('subject', 'body')
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

class MessageDeleteView(OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

class MailingListView(ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'

    def get_queryset(self):
        """Показываем все объекты админам, а обычным пользователям - только свои"""
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        elif self.request.user.is_authenticated:
            return queryset.filter(owner=self.request.user)
        return queryset.none()


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ('start_time', 'end_time', 'status', 'message', 'clients')
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and not user.is_superuser:
            # Ограничиваем выбор клиентов и сообщений только своими
            self.fields['clients'].queryset = Client.objects.filter(owner=user)
            self.fields['message'].queryset = Message.objects.filter(owner=user)


class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form_kwargs(self):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class MailingUpdateView(OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class MailingDeleteView(OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')


def send_mailing_now(request, pk):
    """Отправка рассылки немедленно с записью попытки"""
    mailing = get_object_or_404(Mailing, pk=pk)

    # Логируем начало отправки
    logger.info(f"Запуск ручной отправки рассылки ID: {pk}, пользователь: {request.user.email}")

    # Создаем запись о попытке
    attempt = MailingAttempt.objects.create(
        mailing=mailing,
        status=MailingAttempt.STATUS_SUCCESS,
        server_response='Запущено вручную'
    )

    successful_sends = 0
    failed_sends = 0
    error_message = None

    try:
        # Отправляем письмо каждому клиенту
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
                error_message = str(e)
                # Логируем ошибку для конкретного клиента
                logger.error(f"Ошибка отправки для клиента {client.email}: {e}")

        # Обновляем статус рассылки
        mailing.status = Mailing.STATUS_STARTED
        mailing.save()

        # Обновляем запись попытки
        attempt.server_response = f"Успешно: {successful_sends}, Неудачно: {failed_sends}"
        if failed_sends > 0:
            attempt.status = MailingAttempt.STATUS_FAILED
            attempt.server_response += f". Ошибка: {error_message}"
        attempt.save()

        # Логируем результат
        logger.info(f"Рассылка {pk} завершена: {successful_sends} успешно, {failed_sends} с ошибками")

        if failed_sends == 0:
            messages.success(request, f'Рассылка #{mailing.id} успешно отправлена!')
        else:
            messages.warning(request,
                             f'Рассылка #{mailing.id} отправлена с ошибками: {successful_sends} успешно, {failed_sends} с ошибками')

    except Exception as e:
        # Общая ошибка
        attempt.status = MailingAttempt.STATUS_FAILED
        attempt.server_response = f"Общая ошибка: {str(e)}"
        attempt.save()

        # Логируем критическую ошибку
        logger.critical(f"Критическая ошибка отправки рассылки {pk}: {str(e)}")

        messages.error(request, f'Ошибка отправки: {str(e)}')

    return redirect('mailing:mailing_list')

def statistics(request):
    """Полная статистика по рассылкам пользователя"""
    if not request.user.is_authenticated:
        logger.warning(f"Попытка доступа к статистике без авторизации")
        return redirect('users:login')

    logger.info(f"Пользователь {request.user.email} запросил статистику")

    # Основные данные
    user_mailings = Mailing.objects.filter(owner=request.user)
    user_clients = Client.objects.filter(owner=request.user)
    mailing_attempts = MailingAttempt.objects.filter(mailing__owner=request.user)

    # Общая статистика
    total_mailings = user_mailings.count()
    active_mailings = user_mailings.filter(status=Mailing.STATUS_STARTED).count()
    created_mailings = user_mailings.filter(status=Mailing.STATUS_CREATED).count()
    completed_mailings = user_mailings.filter(status=Mailing.STATUS_COMPLETED).count()

    # Статистика по попыткам
    total_attempts = mailing_attempts.count()
    successful_attempts = mailing_attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count()
    failed_attempts = mailing_attempts.filter(status=MailingAttempt.STATUS_FAILED).count()
    success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0

    # Статистика по клиентам
    total_clients = user_clients.count()
    active_clients = user_clients.annotate(
        mailing_count=Count('mailing', filter=Q(mailing__status=Mailing.STATUS_STARTED))
    ).filter(mailing_count__gt=0).count()

    # Детальная статистика по каждой рассылке
    mailing_stats = []
    for mailing in user_mailings:
        attempts = mailing_attempts.filter(mailing=mailing)
        mailing_stats.append({
            'mailing': mailing,
            'total_attempts': attempts.count(),
            'successful_attempts': attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count(),
            'failed_attempts': attempts.filter(status=MailingAttempt.STATUS_FAILED).count(),
            'last_attempt': attempts.order_by('-attempt_time').first(),
            'clients_count': mailing.clients.count(),
        })

    # Статистика по времени (последние 30 дней)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_attempts = mailing_attempts.filter(attempt_time__gte=thirty_days_ago)

    daily_stats = recent_attempts.extra(
        {'date': "date(attempt_time)"}
    ).values('date').annotate(
        total=Count('id'),
        success=Count('id', filter=Q(status=MailingAttempt.STATUS_SUCCESS)),
        failed=Count('id', filter=Q(status=MailingAttempt.STATUS_FAILED))
    ).order_by('date')

    # Топ клиентов по количеству рассылок
    top_clients = user_clients.annotate(
        mailing_count=Count('mailing')
    ).order_by('-mailing_count')[:10]

    context = {
        # Основная статистика
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'created_mailings': created_mailings,
        'completed_mailings': completed_mailings,

        # Статистика попыток
        'total_attempts': total_attempts,
        'successful_attempts': successful_attempts,
        'failed_attempts': failed_attempts,
        'success_rate': round(success_rate, 2),

        # Статистика клиентов
        'total_clients': total_clients,
        'active_clients': active_clients,

        # Детальная статистика
        'mailing_stats': mailing_stats,
        'daily_stats': list(daily_stats),
        'top_clients': top_clients,

        # Временные периоды
        'thirty_days_ago': thirty_days_ago.date(),
    }

    return render(request, 'mailing/statistics.html', context)

