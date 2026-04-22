# settings.py
from pathlib import Path
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# Seguridad
# =========================
SECRET_KEY = config("DJANGO_SECRET_KEY", default="django-insecure-change-this")

DEBUG = config("DEBUG", default=True, cast=bool)

# ✅ Hosts permitidos (en producción agrega tu dominio)
ALLOWED_HOSTS = [h.strip() for h in config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",") if h.strip()]


# =========================
# Apps instaladas
# =========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "gestion_asociacion",
]


# =========================
# Middleware
# =========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================
# Usuario personalizado
# =========================
AUTH_USER_MODEL = "gestion_asociacion.Usuario"


# =========================
# URLs / WSGI
# =========================
ROOT_URLCONF = "sistema_control_asociacion.urls"
WSGI_APPLICATION = "sistema_control_asociacion.wsgi.application"


# =========================
# Templates
# =========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # ✅ Tus context processors
                "gestion_asociacion.context_processors.excluded_urls",
                "gestion_asociacion.context_processors.static_version",
                "gestion_asociacion.context_processors.user_role",
                'gestion_asociacion.context_processors.contadores_mensajes',
            ],
        },
    },
]


# =========================
# Base de datos MySQL
# =========================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="sistema_web"),
        "USER": config("DB_USER", default="fernando"),
        "PASSWORD": config("DB_PASSWORD", default="Fernan29"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "use_unicode": True,
        },
    }
}


# =========================
# Cache
# =========================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


# =========================
# Sesiones
# =========================
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_AGE = 1800 # 30 minutos
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True

# ✅ En producción pon True (HTTPS)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
SESSION_COOKIE_SAMESITE = "Lax"


# =========================
# CSRF
# =========================
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False

# ✅ En producción pon True (HTTPS)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SAMESITE = "Lax"


# =========================
# Validación de contraseñas
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =========================
# Internacionalización
# =========================
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True


# =========================
# Archivos estáticos
# =========================
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "gestion_asociacion" / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ✅ Control de versiones de static (tu context processor lo usa)
STATIC_VERSION = config("STATIC_VERSION", default="1.0")


# =========================
# ✅ MEDIA (NECESARIO para adjuntos de mensajes)
# =========================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================
# Auth / redirects
# =========================
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/mi_login/"
LOGIN_URL = "/mi_login/"


AUTHENTICATION_BACKENDS = [
    "gestion_asociacion.backends.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]


# =========================
# Email (Brevo SMTP)
# =========================
BREVO_API_KEY = config("BREVO_API_KEY", default="")

DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="Control de Asociación <fernando_mm@tesch.edu.mx>",
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("BREVO_SMTP_HOST", default="smtp-relay.brevo.com")
EMAIL_PORT = config("BREVO_SMTP_PORT", default=587, cast=int)

# ✅ Para Brevo SMTP en 587: TLS=True, SSL=False
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = config("BREVO_SMTP_USER", default="")
EMAIL_HOST_PASSWORD = config("BREVO_SMTP_PASSWORD", default="")

# ✅ Tiempo de validez del token de reset
PASSWORD_RESET_TIMEOUT = 600  # 10 min

# Verificación de correo
EMAIL_VERIFICATION_TIMEOUT = 1800  # 30 min
VERIFICATION_RESEND_COOLDOWN = 20 # 20 segundos entre reenvíos

# =========================
# Extra recomendado (opc.)
# =========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
