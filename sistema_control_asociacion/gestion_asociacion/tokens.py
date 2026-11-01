from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Token de un solo uso lógico para verificar el correo de una cuenta."""

    def _make_hash_value(self, user, timestamp):
        last_login = ""
        if user.last_login:
            last_login = user.last_login.replace(microsecond=0, tzinfo=None)

        return (
            f"{user.pk}{user.password}{last_login}{timestamp}"
            f"{user.is_active}{user.email_verificado}{user.email}"
        )

    def check_token(self, user, token):
        if not user or not token or user.email_verificado:
            return False

        try:
            ts_b36, _hash = token.split("-")
            ts_token = base36_to_int(ts_b36)
        except (ValueError, TypeError):
            return False

        # La firma debe coincidir con el estado actual de la cuenta.
        if not constant_time_compare(
            self._make_token_with_timestamp(user, ts_token, self.secret),
            token,
        ):
            return False

        timeout = getattr(settings, "EMAIL_VERIFICATION_TIMEOUT", 3600)
        elapsed = self._num_seconds(self._now()) - ts_token
        if elapsed < 0 or elapsed > timeout:
            return False

        return True


email_verification_token = EmailVerificationTokenGenerator()
