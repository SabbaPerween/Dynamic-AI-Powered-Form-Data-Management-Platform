# core/decorators.py (NEW FILE)
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from .models import Form, FormPermission

def user_has_permission(required_levels):
    """
    Decorator to check if a user has the required permission level for a form.
    required_levels should be a list, e.g., ['editor', 'admin']
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, form_id, *args, **kwargs):
            form = get_object_or_404(Form, pk=form_id)
            user = request.user

            # Global admin and the form creator always have permission
            if user.role == 'admin' or form.created_by == user:
                return view_func(request, form_id, *args, **kwargs)

            # Check for explicit permission
            try:
                permission = FormPermission.objects.get(form=form, user=user)
                if permission.permission_level in required_levels:
                    return view_func(request, form_id, *args, **kwargs)
            except FormPermission.DoesNotExist:
                pass # Fall through to the error

            # If no permission was found, raise a 404 Not Found error
            raise Http404
        return _wrapped_view
    return decorator