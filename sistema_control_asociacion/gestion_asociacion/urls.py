from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    # =========================
    # Auth
    # =========================
    path("", views.primer_login, name="primer_login"),
    path("mi_login/", views.login_view, name="login"),
    path("registro/", views.registro, name="registro"),
    path("registro/exito/", views.registro_exito, name="registro_exito"),
    path("activar/<uidb64>/<token>/", views.activar_cuenta, name="activar_cuenta"),
    path("reenviar-verificacion/", views.reenviar_verificacion, name="reenviar_verificacion"),
    path("verificar_usuario/", views.verificar_usuario, name="verificar_usuario"),
    path("logout/", views.logout_view, name="logout"),

    # =========================
    # App
    # =========================
    path("dashboard/", views.dashboard, name="dashboard"),
    path("control/", views.control, name="control"),
    path("gestion_cap/", views.gestion_cap, name="gestion_cap"),
    path("gestion/", views.gestion, name="gestion"),

    path("gestion/usuarios/<int:user_id>/", views.usuario_detalle, name="usuario_detalle"),
    path("gestion/usuarios/<int:user_id>/editar/", views.editar_usuario, name="editar_usuario"),
    path("gestion/usuarios/<int:user_id>/cambiar-rol/", views.cambiar_rol_usuario, name="cambiar_rol_usuario"),
    path("promover/<int:user_id>/", views.promover_usuario, name="promover_usuario"),
    path("eliminar/<int:user_id>/", views.eliminar_usuario, name="eliminar_usuario"),

    path("nomina/", views.nomina, name="nomina"),
    path("evaluacion_desem/", views.evaluacion_desem, name="evaluacion_desem"),

    # =========================
    # Comunicación
    # =========================
    path("comunicacion/", views.comunicacion_interna, name="comunicacion_interna"),
    path("comunicacion/admin/", views.comunicacion_admin, name="comunicacion_admin"),
    path("comunicacion/ver/<int:mensaje_id>/", views.ver_mensaje, name="ver_mensaje"),
    path("comunicacion/enviar/miembro/", views.enviar_mensaje_miembro, name="enviar_mensaje_miembro"),
    path("comunicacion/enviar/admin/", views.enviar_mensaje_admin, name="enviar_mensaje_admin"),

    # =========================
    # Papelera (Comunicación)
    # =========================
    path("comunicacion/papelera/", views.papelera, name="papelera"),
    path("comunicacion/<int:mensaje_id>/papelera/", views.mover_a_papelera, name="mover_a_papelera"),
    path("comunicacion/<int:mensaje_id>/restaurar/", views.restaurar_mensaje, name="restaurar_mensaje"),
    path("comunicacion/<int:mensaje_id>/eliminar/", views.eliminar_definitivo, name="eliminar_definitivo"),

    # =========================
    # Password reset
    # =========================
    path("password_reset/", views.CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset_done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="gestion_asociacion/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path("reset/<uidb64>/<token>/", views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path(
        "password_reset_complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="gestion_asociacion/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    # =========================
    # Extras
    # =========================
    path("add_personal/", views.add_personal, name="add_personal"),
    path("add_event/", views.add_event, name="add_event"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)