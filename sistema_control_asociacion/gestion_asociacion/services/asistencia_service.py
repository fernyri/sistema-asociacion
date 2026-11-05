
from django.db import transaction
from django.utils import timezone

from gestion_asociacion.models import (
    Asistencia,
    ConfiguracionAsistencia,
)


def cerrar_asistencias_incompletas_vencidas():
    """
    Cierra las asistencias de días anteriores
    que tengan entrada registrada y no tengan salida.

    No depende de Windows ni de tareas programadas.

    Retorna la cantidad de registros cerrados.
    """

    hoy = timezone.localdate()

    with transaction.atomic():

        config = (
            ConfiguracionAsistencia.objects
            .filter(activa=True)
            .first()
        )

        if config is None:
            return 0

        actualizadas = (
            Asistencia.objects
            .filter(
                fecha__lt=hoy,
                hora_entrada__isnull=False,
                hora_salida__isnull=True,
            )
            .update(
                hora_salida=config.hora_salida_automatica,
                estado="salida_automatica",
                observacion=(
                    "El usuario no registró salida. "
                    "El sistema cerró la asistencia automáticamente."
                ),
            )
        )

    return actualizadas
