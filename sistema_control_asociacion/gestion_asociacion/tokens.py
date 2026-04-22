from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token para verificación de correo.
    Se invalida automáticamente si cambia:
    - password
    - last_login
    - is_active
    """

    def _make_hash_value(self, user, timestamp):
        last_login = ""
        if user.last_login:
            last_login = user.last_login.replace(microsecond=0, tzinfo=None)

        return f"{user.pk}{user.password}{last_login}{timestamp}{user.is_active}"

    def check_token(self, user, token):
        if not (user and token):
            return False

        try:
            ts_b36, _hash = token.split("-")
        except ValueError:
            return False

        try:
            ts_token = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Validar firma/hash
        if not constant_time_compare(
            self._make_token_with_timestamp(user, ts_token, self.secret),
            token,
        ):
            return False

        # Validar expiración
        timeout = getattr(settings, "EMAIL_VERIFICATION_TIMEOUT", 3600)
        now_ts = self._num_seconds(self._now())
        if (now_ts - ts_token) > timeout:
            return False

        return True


email_verification_token = EmailVerificationTokenGenerator()