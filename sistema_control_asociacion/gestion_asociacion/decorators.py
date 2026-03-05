# decorators.py
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages


def admin_only(view_func):
    """
    ✅ Decorador: permite el acceso solo a Administradores o superusuarios.
    Usa request.user.is_admin() del modelo Usuario.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # ✅ Si no está autenticado, manda a login
        if not request.user.is_authenticated:
            messages.error(request, "⚠️ Debes iniciar sesión para acceder a esta página.")
            return redirect("primer_login")

        # ✅ Evita truene si por alguna razón is_admin no existe
        is_admin = getattr(request.user, "is_admin", None)
        is_admin_value = is_admin() if callable(is_admin) else False

        if request.user.is_superuser or is_admin_value:
            return view_func(request, *args, **kwargs)

        # ✅ No autorizado
        messages.error(request, "❌ No tienes permiso para acceder a esta página.")
        return HttpResponseForbidden("Acceso denegado")

    return wrapper


def role_required(*roles):
    """
    ✅ Decorador: permite acceso solo a usuarios con uno o varios roles específicos o superusuarios.
    Ejemplos:
        @role_required("Miembro")
        @role_required("Administrador", "Miembro")
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "⚠️ Debes iniciar sesión para acceder a esta página.")
                return redirect("primer_login")

            user_role = getattr(request.user, "rol", "")

            if request.user.is_superuser or user_role in roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "❌ No tienes permiso para acceder a esta página.")
            return HttpResponseForbidden("Acceso denegado")

        return wrapper
    return decorator
