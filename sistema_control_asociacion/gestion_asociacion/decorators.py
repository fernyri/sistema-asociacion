# decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_only(view_func):
    """
    ✅ Permite acceso a:
    - Usuarios con rol "Administrador"
    - Usuarios con rol "Dios"
    - Superusuarios de Django
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "⚠️ Debes iniciar sesión para acceder a esta página.")
            return redirect("primer_login")

        user_role = getattr(request.user, "rol", "")

        if request.user.is_superuser or user_role in ["Dios", "Administrador"]:
            return view_func(request, *args, **kwargs)

        messages.error(request, "❌ No tienes permiso para acceder a esta página.")
        return redirect("dashboard")

    return wrapper


def dios_only(view_func):
    """
    ✅ Permite acceso solo a:
    - Usuarios con rol "Dios"
    - Superusuarios de Django
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "⚠️ Debes iniciar sesión para acceder a esta página.")
            return redirect("primer_login")

        user_role = getattr(request.user, "rol", "")

        if request.user.is_superuser or user_role == "Dios":
            return view_func(request, *args, **kwargs)

        messages.error(request, "❌ Esta acción solo está permitida para el rol Dios.")
        return redirect("dashboard")

    return wrapper


def role_required(*roles):
    """
    ✅ Permite acceso solo a usuarios con uno o varios roles específicos
    o superusuarios.

    Ejemplos:
        @role_required("Miembro")
        @role_required("Administrador", "Miembro")
        @role_required("Dios", "Administrador")
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
            return redirect("dashboard")

        return wrapper
    return decorator