from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.models import User
import logging

# Configurar el logger
logger = logging.getLogger(__name__)

# Esta señal se ejecutará después de que un usuario cambie su contraseña
@receiver(post_save, sender=User)
def password_changed(sender, instance, created, **kwargs):
    if not created:  # Si el usuario ya existe y no es nuevo
        logger.info(f"Contraseña actualizada para el usuario: {instance.username}")
