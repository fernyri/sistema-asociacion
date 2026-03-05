from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Usuario, Asistencia, Tarea, Reporte, Notification, AttendanceSummary, Personal, Evento


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Tabla principal
    list_display = ("username", "email", "rol", "is_active", "is_staff", "date_joined")
    list_filter = ("rol", "is_active", "is_staff", "is_superuser")
    ordering = ("username",)
    list_per_page = 20

    # Búsqueda (incluye el campo real case-insensitive)
    search_fields = ("username", "username_norm", "email", "first_name", "last_name")

    # read-only (porque lo generas en save())
    readonly_fields = ("username_norm", "last_login", "date_joined")

    # Campos extra en el formulario admin
    fieldsets = (
        (None, {"fields": ("username", "username_norm", "password")}),
        (_("Información personal"), {"fields": ("first_name", "last_name", "email", "telefono", "direccion", "genero", "fecha_nacimiento")}),
        (_("Permisos"), {"fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Fechas importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "rol", "password1", "password2"),
        }),
    )


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "fecha", "hora_entrada", "hora_salida")
    list_filter = ("fecha",)
    search_fields = ("usuario__username", "usuario__username_norm", "usuario__email")
    ordering = ("-fecha",)


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "descripcion", "fecha_asignada", "fecha_limite")
    list_filter = ("fecha_asignada", "fecha_limite")
    search_fields = ("usuario__username", "usuario__username_norm", "descripcion")


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ("titulo", "fecha_creacion")
    search_fields = ("titulo", "contenido")
    ordering = ("-fecha_creacion",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("message", "created_at")
    ordering = ("-created_at",)


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ("present", "absent", "late", "date")
    ordering = ("-date",)


# Si ya usas Personal/Evento en la app, mejor también registrarlos
@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "departamento", "fecha_creacion")
    list_filter = ("departamento",)
    search_fields = ("nombre", "email")
    ordering = ("nombre",)


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "fecha", "fecha_creacion")
    list_filter = ("fecha",)
    search_fields = ("titulo", "descripcion")
    ordering = ("-fecha",)
