from django.core.exceptions import PermissionDenied

class OwnerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user and not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
