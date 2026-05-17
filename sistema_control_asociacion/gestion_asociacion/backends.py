from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailAuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        # Permitir login con email
        if username is None:
            username = kwargs.get("email")

        if username is None or password is None:
            return None

        try:
            user = UserModel.objects.get(email__iexact=username.strip())

            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        except UserModel.DoesNotExist:
            return None

        return None