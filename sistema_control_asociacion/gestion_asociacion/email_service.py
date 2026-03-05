from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from gestion_asociacion.brevo_email import enviar_email_brevo


def enviar_email(asunto: str, html: str, destinatario: str, texto: str = "") -> bool:
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=texto or " ",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario],
        )
        msg.attach_alternative(html, "text/html")
        msg.send()
        return True
    except Exception as e:
        print("❌ Error SMTP:", e)

        if getattr(settings, "USE_BREVO_API_FALLBACK", False):
            return enviar_email_brevo(asunto, html, destinatario)

        return False
