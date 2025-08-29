from django.contrib import admin
from mailing.models import Client, Message, Mailing, MailingAttempt

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'comment')
    list_filter = ('email',)
    search_fields = ('email', 'full_name')

    def get_queryset(self, request):
        """Показываем все объекты суперпользователю, остальным - только свои"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'body')

    def get_queryset(self, request):
        """Показываем все объекты суперпользователю, остальным - только свои"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'status', 'message', 'owner')
    list_filter = ('status', 'start_time')
    actions = ['disable_selected_mailings']

    def disable_selected_mailings(self, request, queryset):
        """Action для отключения выбранных рассылок"""
        updated = queryset.update(status=Mailing.STATUS_COMPLETED)
        self.message_user(request, f"Отключено {updated} рассылок")

    disable_selected_mailings.short_description = "Отключить выбранные рассылки"

    def has_change_permission(self, request, obj=None):
        """Запрещаем редактирование чужих рассылок"""
        if obj and obj.owner != request.user and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление чужих рассылок"""
        if obj and obj.owner != request.user and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_queryset(self, request):
        """Показываем все рассылки менеджерам, но только свои обычным пользователям"""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('mailing.can_view_all_mailings'):
            return qs
        return qs.filter(owner=request.user)

@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('attempt_time', 'status', 'mailing', 'server_response')
    list_filter = ('status', 'attempt_time')

    def get_queryset(self, request):
        """Показываем все объекты суперпользователю, остальным - только свои"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)