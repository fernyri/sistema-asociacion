import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings


def enviar_email_brevo(asunto: str, html: str, destinatario: str) -> bool:
    if not getattr(settings, "BREVO_API_KEY", ""):
        raise RuntimeError("BREVO_API_KEY no está configurada en settings.py / .env")

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": destinatario}],
        sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "Sistema de Gestión"},
        subject=asunto,
        html_content=html,
    )

    try:
        api_instance.send_transac_email(email)
        return True
    except ApiException as e:
        print("❌ Error Brevo:", e)
        return False
