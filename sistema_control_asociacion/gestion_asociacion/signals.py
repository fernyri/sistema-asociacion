from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from .models import BitacoraAcceso

User = get_user_model()

logger = logging.getLogger(__name__)


def obtener_ip_cliente(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def registrar_inicio_sesion(sender, request, user, **kwargs):
    # Cierra sesiones anteriores abiertas del mismo usuario
    BitacoraAcceso.objects.filter(
        usuario=user,
        hora_salida__isnull=True
    ).update(
        hora_salida=timezone.now()
    )

    # Crea una nueva sesión activa
    BitacoraAcceso.objects.create(
        usuario=user,
        hora_entrada=timezone.now(),
        ip=obtener_ip_cliente(request)
    )


@receiver(user_logged_out)
def registrar_cierre_sesion(sender, request, user, **kwargs):
    if not user:
        return

    acceso = (
        BitacoraAcceso.objects
        .filter(usuario=user, hora_salida__isnull=True)
        .order_by("-hora_entrada")
        .first()
    )

    if acceso:
        acceso.hora_salida = timezone.now()
        acceso.save(update_fields=["hora_salida"])


@receiver(post_save, sender=User)
def password_changed(sender, instance, created, **kwargs):
    if not created:
        logger.info(f"Contraseña actualizada para el usuario: {instance.username}")