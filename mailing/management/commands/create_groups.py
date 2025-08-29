from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Create manager group with permissions'

    def handle(self, *args, **options):
        # Создаем группу менеджеров
        manager_group, created = Group.objects.get_or_create(name='Менеджеры')

        # Добавляем КАСТОМНЫЕ права которые мы создали в моделях
        permissions = Permission.objects.filter(
            codename__in=[
                'can_view_all_messages',  # Просмотр всех сообщений
                'can_view_all_clients',  # Просмотр всех клиентов
                'can_view_all_mailings',  # Просмотр всех рассылок
                'can_disable_mailings',  # Отключение рассылок
            ]
        )

        for perm in permissions:
            manager_group.permissions.add(perm)

        self.stdout.write(
            self.style.SUCCESS('Группа "Менеджеры" создана с правами:')
        )
        for perm in permissions:
            self.stdout.write(f"  - {perm.name}")