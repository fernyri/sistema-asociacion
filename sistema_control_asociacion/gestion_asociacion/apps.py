from django.apps import AppConfig

class GestionAsociacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_asociacion'

    def ready(self):
        import gestion_asociacion.signals  # Registrar las señales
