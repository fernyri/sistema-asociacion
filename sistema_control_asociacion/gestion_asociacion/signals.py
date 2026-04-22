from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging
from django.utils.timezone import now

from .models import BitacoraAcceso

User = get_user_model()

# Configurar el logger
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def password_changed(sender, instance, created, **kwargs):
    if not created:
        logger.info(f"Contraseña actualizada para el usuario: {instance.username}")


@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):

    # cerrar sesiones abiertas anteriores
    BitacoraAcceso.objects.filter(
        usuario=user,
        hora_salida__isnull=True
    ).update(hora_salida=now())

    BitacoraAcceso.objects.create(
        usuario=user,
        hora_entrada=now(),
        ip=request.META.get('REMOTE_ADDR')
    )


@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):

    ultimo_registro = BitacoraAcceso.objects.filter(
        usuario=user,
        hora_salida__isnull=True
    ).last()

    if ultimo_registro:
        ultimo_registro.hora_salida = now()
        ultimo_registro.save()