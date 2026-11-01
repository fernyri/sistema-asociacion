import uuid
from datetime import timedelta

from gestion_asociacion.models import Mensaje


def limpiar_asunto(asunto):
    asunto = (asunto or "").strip()

    while asunto.lower().startswith("re:"):
        asunto = asunto[3:].strip()

    return asunto or "Sin asunto"


mensajes = list(
    Mensaje.objects
    .all()
    .order_by("creado_en", "id")
)

grupos = {}
actualizados = 0

for mensaje in mensajes:

    asunto_limpio = limpiar_asunto(
        mensaje.asunto
    )

    # Si alguno de los participantes fue eliminado,
    # se conserva el mensaje como una conversación individual.
    if (
        mensaje.remitente_id is None
        or mensaje.destinatario_id is None
    ):
        mensaje.hilo_id = (
            mensaje.hilo_id
            or uuid.uuid4()
        )

        mensaje.asunto = asunto_limpio

        mensaje.save(
            update_fields=[
                "hilo_id",
                "asunto",
            ]
        )

        actualizados += 1
        continue

    participante_1, participante_2 = sorted([
        mensaje.remitente_id,
        mensaje.destinatario_id,
    ])

    clave = (
        participante_1,
        participante_2,
        asunto_limpio.casefold(),
    )

    grupos.setdefault(
        clave,
        []
    ).append(
        mensaje
    )


for clave, mensajes_grupo in grupos.items():

    hilo_actual = None
    fecha_anterior = None

    for mensaje in mensajes_grupo:

        asunto_limpio = limpiar_asunto(
            mensaje.asunto
        )

        iniciar_nuevo_hilo = (
            hilo_actual is None
            or (
                fecha_anterior is not None
                and (
                    mensaje.creado_en
                    - fecha_anterior
                ) > timedelta(days=30)
            )
        )

        if iniciar_nuevo_hilo:
            hilo_actual = uuid.uuid4()

        mensaje.hilo_id = hilo_actual
        mensaje.asunto = asunto_limpio

        mensaje.save(
            update_fields=[
                "hilo_id",
                "asunto",
            ]
        )

        actualizados += 1
        fecha_anterior = mensaje.creado_en


print(
    f"Listo. Se actualizaron "
    f"{actualizados} mensaje(s)."
)
