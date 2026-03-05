from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from gestion_asociacion import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Administración
    path("admin/", admin.site.urls),

    # Autenticación
    path("login/", auth_views.LoginView.as_view(template_name="gestion_asociacion/primer_login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Registro
    path("registro/", views.registro, name="registro"),

    # Dashboard principal
    path("dashboard/", views.dashboard, name="dashboard"),

    # Redirección desde la raíz al login
    path("", auth_views.LoginView.as_view(template_name="gestion_asociacion/primer_login.html"), name="root"),

    # Rutas de tu app
    path("", include("gestion_asociacion.urls")),
]

# ✅ Servir media en desarrollo (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
