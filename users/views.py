from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy, reverse
from .forms import UserRegisterForm
from .models import User
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.contrib import messages
import secrets

class UserLoginView(LoginView):
    template_name = 'users/login.html'


@csrf_protect
def custom_logout(request):
    logout(request)
    return redirect('index')


class UserRegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance

        # Генерируем токен подтверждения
        user.verification_token = secrets.token_urlsafe(32)
        user.save()

        # Отправляем письмо подтверждения
        verification_url = self.request.build_absolute_uri(
            reverse('users:verify_email', kwargs={'token': user.verification_token})
        )

        send_mail(
            'Подтверждение email',
            f'Перейдите по ссылке для подтверждения: {verification_url}',
            'noreply@mailing-service.ru',
            [user.email],
            fail_silently=False,
        )

        return response


def verify_email(request, token):
    try:
        user = User.objects.get(verification_token=token)
        user.email_verified = True
        user.verification_token = None
        user.save()
        messages.success(request, 'Email успешно подтвержден!')
    except User.DoesNotExist:
        messages.error(request, 'Неверная ссылка подтверждения')

    return redirect('users:login')