from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.urls import reverse
from users.models import User
import secrets

class Command(BaseCommand):
    help = 'Send verification email to new users'

    def handle(self, *args, **options):
        # При регистрации будет вызываться эта команда
        pass