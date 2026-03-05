# context_processors.py
from django.conf import settings
from django.db.models import Q
from .models import Mensaje


def contadores_mensajes(request):
    """
    Contadores globales:
    - no_leidos: mensajes no leídos (excluye papelera)
    - papelera_count: mensajes en papelera del usuario
    """
    if not request.user.is_authenticated:
        return {
            "no_leidos": 0,
            "papelera_count": 0,
        }

    no_leidos = Mensaje.objects.filter(
        destinatario=request.user,
        leido=False,
        en_papelera=False
    ).count()

    papelera_count = Mensaje.objects.filter(
        en_papelera=True
    ).filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).count()

    return {
        "no_leidos": no_leidos,
        "papelera_count": papelera_count,
    }


def excluded_urls(request):
    return {
        "excluded_urls": [
            "primer_login",
            "registro",
        ]
    }


def static_version(request):
    return {
        "STATIC_VERSION": getattr(settings, "STATIC_VERSION", "1.0")
    }


def user_role(request):
    if not request.user.is_authenticated:
        return {"user_role": "Invitado"}

    return {"user_role": getattr(request.user, "rol", "No definido")}
