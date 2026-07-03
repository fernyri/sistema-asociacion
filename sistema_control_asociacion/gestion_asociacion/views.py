# views.py
from datetime import datetime, time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from .tokens import email_verification_token
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.contrib.sessions.models import Session
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .decorators import admin_only
from .forms import MensajeForm, RegistroForm, CapacitacionForm, CapacitacionAsignadaForm
from .models import (
    Asistencia,
    ConfiguracionAsistencia,
    BitacoraAcceso,
    Evento,
    Mensaje,
    Notification,
    Personal,
    Usuario,
    Capacitacion,
    CapacitacionAsignada,
)

User = get_user_model()


# ============================================================
# Helpers
# ============================================================

def obtener_configuracion_asistencia():
    config = ConfiguracionAsistencia.objects.filter(activa=True).first()

    if not config:
        config = ConfiguracionAsistencia.objects.create(
            nombre="Configuración general",
            hora_entrada=time(9, 0),
            tolerancia_minutos=15,
            hora_salida_automatica=time(23, 59),
            activa=True
        )

    return config


def obtener_hora_limite_retardo():
    config = obtener_configuracion_asistencia()
    return config.hora_limite_retardo()


def cerrar_asistencias_incompletas_vencidas():
    hoy = timezone.localdate()
    config = obtener_configuracion_asistencia()

    asistencias_pendientes = Asistencia.objects.filter(
        fecha__lt=hoy,
        hora_entrada__isnull=False,
        hora_salida__isnull=True
    )

    for asistencia in asistencias_pendientes:
        asistencia.hora_salida = config.hora_salida_automatica
        asistencia.estado = "salida_automatica"
        asistencia.observacion = (
            "El usuario no registró salida. "
            "El sistema cerró la asistencia automáticamente."
        )
        asistencia.save(update_fields=["hora_salida", "estado", "observacion"])

def _es_admin(u: Usuario) -> bool:
    return getattr(u, "rol", "") in ["Administrador", "Dios"]


def _mensajes_recibidos(user: Usuario):
    return (
        Mensaje.objects.filter(destinatario=user, en_papelera=False)
        .select_related("remitente", "destinatario")
        .order_by("-creado_en")
    )


def _mensajes_enviados(user: Usuario):
    return (
        Mensaje.objects.filter(remitente=user, en_papelera=False)
        .select_related("remitente", "destinatario")
        .order_by("-creado_en")
    )

@login_required
def registrar_entrada(request):
    if request.method != "POST":
        return redirect("dashboard")

    if getattr(request.user, "rol", "") != "Miembro":
        messages.error(request, "Solo los miembros pueden registrar asistencia.")
        return redirect("dashboard")

    cerrar_asistencias_incompletas_vencidas()

    hoy = timezone.localdate()
    hora_actual = timezone.localtime().time()
    hora_limite_retardo = obtener_hora_limite_retardo()
    config_asistencia = obtener_configuracion_asistencia()
    hora_limite_extraordinario = config_asistencia.hora_limite_extraordinario

    asistencia = Asistencia.objects.filter(
        usuario=request.user,
        fecha=hoy
    ).first()

    if asistencia and asistencia.hora_entrada:
        messages.warning(request, "Ya registraste tu entrada de hoy.")
        return redirect("dashboard")

    if not asistencia:
        asistencia = Asistencia(usuario=request.user, fecha=hoy)

    asistencia.hora_entrada = hora_actual
    asistencia.hora_salida = None
    asistencia.estado = "salida_pendiente"

    if hora_actual >= hora_limite_extraordinario:
        asistencia.observacion = "Entrada registrada fuera del horario laboral."
    elif hora_actual > hora_limite_retardo:
         asistencia.observacion = "Entrada registrada con retardo."
    else:
         asistencia.observacion = "Entrada registrada correctamente."

    asistencia.save()

    messages.success(request, "Entrada registrada correctamente.")
    return redirect("dashboard")


@login_required
def registrar_salida(request):
    if request.method != "POST":
        return redirect("dashboard")

    if getattr(request.user, "rol", "") != "Miembro":
        messages.error(request, "Solo los miembros pueden registrar asistencia.")
        return redirect("dashboard")

    cerrar_asistencias_incompletas_vencidas()

    hoy = timezone.localdate()
    hora_actual = timezone.localtime().time()
    hora_limite_retardo = obtener_hora_limite_retardo()
    config_asistencia = obtener_configuracion_asistencia()
    hora_limite_extraordinario = config_asistencia.hora_limite_extraordinario

    asistencia = Asistencia.objects.filter(
        usuario=request.user,
        fecha=hoy
    ).first()

    if not asistencia or not asistencia.hora_entrada:
        messages.error(request, "Primero debes registrar tu entrada.")
        return redirect("dashboard")

    if asistencia.hora_salida:
        messages.warning(request, "Ya registraste tu salida de hoy.")
        return redirect("dashboard")

    if hora_actual < asistencia.hora_entrada:
        messages.error(request, "La hora de salida no puede ser menor a la hora de entrada.")
        return redirect("dashboard")

    asistencia.hora_salida = hora_actual
    asistencia.estado = "asistencia_completa"

    if asistencia.hora_entrada >= hora_limite_extraordinario:
        asistencia.observacion = "Asistencia registrada fuera del horario laboral configurado."
    elif asistencia.hora_entrada > hora_limite_retardo:
        asistencia.observacion = "Asistencia completa con retardo."
    else:
        asistencia.observacion = "Asistencia completa."

    asistencia.save(update_fields=["hora_salida", "estado", "observacion"])

    messages.success(request, "Salida registrada correctamente.")
    return redirect("dashboard")


def _user_puede_ver_mensaje(user: Usuario, msg: Mensaje) -> bool:
    return msg.remitente_id == user.id or msg.destinatario_id == user.id


def enviar_correo_verificacion(request, user: Usuario):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)

    activation_link = request.build_absolute_uri(
        reverse("activar_cuenta", kwargs={"uidb64": uid, "token": token})
    )

    context = {
        "user": user,
        "activation_link": activation_link,
        "site_name": "Control de Asociación",
        "timeout_minutes": int(getattr(settings, "EMAIL_VERIFICATION_TIMEOUT", 3600) / 60),
    }

    subject = "Verifica tu cuenta - Control de Asociación"
    html_content = render_to_string("gestion_asociacion/email_verificacion.html", context)
    text_content = render_to_string("gestion_asociacion/email_verificacion.txt", context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


# ============================================================
# Password reset (SMTP + HTML)
# ============================================================
class CustomPasswordResetView(PasswordResetView):
    template_name = "gestion_asociacion/password_reset.html"
    html_email_template_name = "gestion_asociacion/password_reset_email.html"
    subject_template_name = "gestion_asociacion/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        messages.success(
            self.request,
            "✅ Si el correo está registrado, recibirás instrucciones para restablecer tu contraseña."
        )
        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "gestion_asociacion/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)

        user = form.user
        now = timezone.now()

        for s in Session.objects.filter(expire_date__gt=now):
            data = s.get_decoded()
            if str(data.get("_auth_user_id")) == str(user.pk):
                s.delete()

        messages.success(
            self.request,
            "✅ Tu contraseña ha sido cambiada correctamente. Por seguridad se cerraron tus sesiones activas."
        )
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"⚠️ Error en {field}: {error}")
        messages.error(self.request, "❌ Ocurrió un error. Verifica los datos e intenta de nuevo.")
        return super().form_invalid(form)


# ============================================================
# Auth / Login / Registro / Verificación
# ============================================================
def primer_login(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return render(request, "gestion_asociacion/primer_login.html")


def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False
                    user.save()

                    enviar_correo_verificacion(request, user)

                messages.success(
                    request,
                    "✅ Tu cuenta fue creada. Revisa tu correo para verificarla antes de iniciar sesión."
                )
                return redirect("registro_exito")

            except IntegrityError:
                messages.error(request, "El usuario o correo ya están registrados.")
            except Exception:
                messages.error(
                    request,
                    "La cuenta se creó, pero hubo un problema al enviar el correo de verificación. Intenta más tarde."
                )

        for field, errs in form.errors.items():
            for err in errs:
                messages.error(request, f"{field}: {err}")
    else:
        form = RegistroForm()

    return render(request, "gestion_asociacion/registro.html", {"form": form})


def registro_exito(request):
    return render(request, "gestion_asociacion/auth_status.html", {
        "titulo": "Revisa tu correo",
        "mensaje": (
            "Tu cuenta fue creada correctamente. Te enviamos un enlace de verificación "
            "a tu correo electrónico. Debes activar tu cuenta antes de iniciar sesión."
        ),
        "boton_texto": "Ir al login",
        "boton_url": reverse("login"),
        "tipo": "success",
    })


def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        messages.success(request, "Tu cuenta ha sido verificada correctamente. Ya puedes iniciar sesión.")
        return render(request, "gestion_asociacion/auth_status.html", {
            "titulo": "Cuenta verificada",
            "mensaje": "Tu cuenta fue activada correctamente. Ya puedes iniciar sesión.",
            "boton_texto": "Iniciar sesión",
            "boton_url": reverse("login"),
            "tipo": "success",
        })

    messages.error(request, "El enlace de verificación no es válido o ya expiró.")
    return render(request, "gestion_asociacion/auth_status.html", {
        "titulo": "Enlace inválido o expirado",
        "mensaje": "El enlace de verificación no es válido, ya fue usado o expiró. Puedes solicitar uno nuevo.",
        "boton_texto": "Reenviar verificación",
        "boton_url": reverse("reenviar_verificacion"),
        "tipo": "danger",
    })

def reenviar_verificacion(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()

        if not email:
            messages.error(request, "⚠️ Debes escribir tu correo electrónico.")
            return redirect("reenviar_verificacion")

        user = Usuario.objects.filter(email__iexact=email).first()

        # respuesta genérica por seguridad
        generic_response = {
            "titulo": "Revisa tu correo",
            "mensaje": (
                "Si existe una cuenta pendiente de verificación con ese correo, "
                "te enviamos un nuevo enlace para activarla."
            ),
            "boton_texto": "Volver al login",
            "boton_url": reverse("login"),
            "tipo": "primary",
        }

        if not user:
            return render(request, "gestion_asociacion/auth_status.html", generic_response)

        if user.is_active:
            return render(request, "gestion_asociacion/auth_status.html", {
                "titulo": "Cuenta ya verificada",
                "mensaje": "Esta cuenta ya está activa. Ya puedes iniciar sesión.",
                "boton_texto": "Ir al login",
                "boton_url": reverse("login"),
                "tipo": "success",
            })

        cooldown = getattr(settings, "VERIFICATION_RESEND_COOLDOWN", 60)
        cache_key = f"email_verify_resend:{user.pk}"

        if cache.get(cache_key):
            return render(request, "gestion_asociacion/auth_status.html", {
                "titulo": "Espera un momento",
                "mensaje": (
                    f"Ya se solicitó un enlace recientemente. "
                    f"Espera {cooldown} segundos antes de volver a intentarlo."
                ),
                "boton_texto": "Volver al login",
                "boton_url": reverse("login"),
                "tipo": "danger",
            })

        try:
            enviar_correo_verificacion(request, user)
            cache.set(cache_key, True, timeout=cooldown)
        except Exception:
            messages.error(
                request,
                "⚠️ No se pudo reenviar el correo en este momento. Intenta más tarde."
            )
            return redirect("reenviar_verificacion")

        return render(request, "gestion_asociacion/auth_status.html", generic_response)

    return render(request, "gestion_asociacion/reenviar_verificacion.html")

def obtener_ip_cliente(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def login_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password")

        context = {
            "email_value": email
        }

        user_obj = Usuario.objects.filter(email__iexact=email).first()

        if user_obj is None:
            messages.error(
                request,
                "El correo no existe.",
                extra_tags="email_not_found"
            )
            return render(request, "gestion_asociacion/primer_login.html", context)

        if not user_obj.is_active:
            messages.error(
                request,
                "Tu cuenta no ha sido verificada. Revisa tu correo o solicita un nuevo enlace.",
                extra_tags="email_unverified"
            )
            return render(request, "gestion_asociacion/primer_login.html", context)

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            return redirect(settings.LOGIN_REDIRECT_URL)

        messages.error(
            request,
            "Contraseña incorrecta.",
            extra_tags="password_error"
        )
        return render(request, "gestion_asociacion/primer_login.html", context)

    return render(request, "gestion_asociacion/primer_login.html")

@login_required
def logout_view(request):
    acceso = (
        BitacoraAcceso.objects
        .filter(usuario=request.user, hora_salida__isnull=True)
        .order_by("-hora_entrada")
        .first()
    )

    if acceso:
        acceso.hora_salida = timezone.now()
        acceso.save(update_fields=["hora_salida"])

    auth_logout(request)
    return redirect("login")

# ============================================================
# Dashboard
# ============================================================
@login_required
def dashboard(request):
    cerrar_asistencias_incompletas_vencidas()
    rol_usuario = getattr(request.user, "rol", "No definido")


    # ============================================================
    # DASHBOARD MIEMBRO
    # ============================================================
    if rol_usuario == "Miembro":
        hoy = timezone.localdate()

        ultimo_acceso = (
            BitacoraAcceso.objects
            .filter(usuario=request.user)
            .order_by("-hora_entrada")
            .first()
        )

        sesiones_activas = (
            BitacoraAcceso.objects
            .filter(usuario=request.user, hora_salida__isnull=True)
            .order_by("-hora_entrada")
        )

        ultimas_asistencias = (
            Asistencia.objects
            .filter(usuario=request.user)
            .order_by("-fecha", "-hora_entrada")[:10]
        )

        asistencia_hoy = (
            Asistencia.objects
            .filter(usuario=request.user, fecha=hoy)
            .first()
        )

        mensajes_no_leidos = Mensaje.objects.filter(
            destinatario=request.user,
            leido=False,
            en_papelera=False
        ).count()

        capacitaciones_miembro = (
            CapacitacionAsignada.objects
            .select_related("capacitacion", "usuario")
            .filter(usuario=request.user)
            .order_by("-fecha_asignacion")
        )

        cap_pendientes = capacitaciones_miembro.filter(estado="pendiente").count()
        cap_en_proceso = capacitaciones_miembro.filter(estado="en_proceso").count()
        cap_aprobadas = capacitaciones_miembro.filter(estado="aprobada").count()
        cap_vencidas = sum(
            1 for cap in capacitaciones_miembro
            if cap.estado == "vencida" or cap.esta_vencida
        )

        context = {
            "user": request.user,
            "user_role": rol_usuario,
            "ultimo_acceso": ultimo_acceso,
            "sesiones_activas": sesiones_activas,
            "total_sesiones_activas": sesiones_activas.count(),
            "ultimas_asistencias": ultimas_asistencias,
            "asistencia_hoy": asistencia_hoy,
            "mensajes_no_leidos": mensajes_no_leidos,
            "capacitaciones_miembro": capacitaciones_miembro,
            "cap_pendientes": cap_pendientes,
            "cap_en_proceso": cap_en_proceso,
            "cap_aprobadas": cap_aprobadas,
            "cap_vencidas": cap_vencidas,
        }

        return render(request, "gestion_asociacion/dashboard_miembro.html", context)

    # ============================================================
    # DASHBOARD ADMIN / DIOS
    # ============================================================
    hoy = timezone.localdate()
    config_asistencia = obtener_configuracion_asistencia()
    hora_limite_retardo = config_asistencia.hora_limite_retardo()

    miembros_activos = Usuario.objects.filter(
        rol="Miembro",
        is_active=True
    )

    asistencias_hoy = Asistencia.objects.filter(
        fecha=hoy,
        usuario__rol="Miembro",
        usuario__is_active=True
    )

    presentes = (
        asistencias_hoy
        .filter(hora_entrada__isnull=False)
        .values("usuario")
        .distinct()
        .count()
    )

    hora_limite_extraordinario = config_asistencia.hora_limite_extraordinario

    retardos = (
        asistencias_hoy
        .filter(
            hora_entrada__gt=hora_limite_retardo,
            hora_entrada__lt=hora_limite_extraordinario
        )
        .values("usuario")
        .distinct()
        .count()
    )

    incompletas = (
    asistencias_hoy
    .filter(
        hora_entrada__isnull=False,
        hora_salida__isnull=True
    )
    .values("usuario")
    .distinct()
    .count()
)

    usuarios_presentes_ids = (
        asistencias_hoy
        .filter(hora_entrada__isnull=False)
        .values_list("usuario_id", flat=True)
    )

    ausentes = (
        miembros_activos
        .exclude(id__in=usuarios_presentes_ids)
        .count()
    )

    attendance_records = (
        Asistencia.objects
        .select_related("usuario")
        .order_by("-fecha", "-hora_entrada")[:10]
    )

    notifications = (
        Notification.objects
        .all()
        .order_by("-created_at")[:5]
    )

    ultimos_accesos = (
        BitacoraAcceso.objects
        .select_related("usuario")
        .order_by("-hora_entrada")[:20]
    )

    usuarios_conectados = (
        BitacoraAcceso.objects
        .filter(hora_salida__isnull=True)
        .select_related("usuario")
        .order_by("-hora_entrada")
    )

    context = {
        "notifications": notifications,
        "attendance_records": attendance_records,
        "ultimos_accesos": ultimos_accesos,
        "usuarios_conectados": usuarios_conectados,
        "total_usuarios_conectados": usuarios_conectados.count(),

        # Contadores dinámicos del día
        "presentes": presentes,
        "ausentes": ausentes,
        "retardos": retardos,
        "incompletas": incompletas, 
        "fecha_resumen": hoy,
        "hora_limite_retardo": hora_limite_retardo,
        "config_asistencia": config_asistencia,


        "user": request.user,
        "user_role": rol_usuario,
    }

    return render(request, "gestion_asociacion/dashboard.html", context)

# ============================================================
# Gestión (Admin) - Lista y Perfil
# ============================================================
@login_required
@admin_only
def gestion(request):
    usuarios = Usuario.objects.order_by("username")

    return render(request, "gestion_asociacion/gestion.html", {
        "miembros": usuarios,
        "user_role": getattr(request.user, "rol", ""),
    })


@login_required
@admin_only
def usuario_detalle(request, user_id: int):
    usuario = Usuario.objects.filter(id=user_id).first()
    if not usuario:
        messages.warning(request, "El usuario no existe (posiblemente fue eliminado).")
        return redirect("gestion")

    return render(request, "gestion_asociacion/usuario_detalle.html", {
        "usuario_obj": usuario,
        "user_role": getattr(request.user, "rol", ""),
    })

@login_required
@admin_only
def editar_usuario(request, user_id: int):
    usuario = Usuario.objects.filter(id=user_id).first()
    if not usuario:
        messages.warning(request, "El usuario no existe.")
        return redirect("gestion")

    user_role = getattr(request.user, "rol", "")

    if usuario.id == request.user.id:
        messages.error(request, "No puedes editar tu propio usuario desde esta vista.")
        return redirect("usuario_detalle", user_id=user_id)

    if getattr(usuario, "rol", "") == "Dios":
        messages.error(request, "No puedes editar a un usuario con rol Dios desde esta vista.")
        return redirect("usuario_detalle", user_id=user_id)

    if user_role == "Administrador" and getattr(usuario, "rol", "") != "Miembro":
        messages.error(request, "Solo puedes editar usuarios con rol Miembro.")
        return redirect("usuario_detalle", user_id=user_id)

    if getattr(usuario, "rol", "") == "Administrador" and user_role != "Dios":
        messages.error(request, "Solo un usuario con rol Dios puede editar administradores.")
        return redirect("usuario_detalle", user_id=user_id)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        telefono = (request.POST.get("telefono") or "").strip()
        direccion = (request.POST.get("direccion") or "").strip()
        genero = (request.POST.get("genero") or "").strip()
        fecha_nacimiento = (request.POST.get("fecha_nacimiento") or "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not username:
            messages.error(request, "El nombre de usuario es obligatorio.")
            return redirect("editar_usuario", user_id=user_id)

        if not first_name:
            messages.error(request, "El nombre es obligatorio.")
            return redirect("editar_usuario", user_id=user_id)

        if not last_name:
            messages.error(request, "El apellido es obligatorio.")
            return redirect("editar_usuario", user_id=user_id)

        if not email:
            messages.error(request, "El correo electrónico es obligatorio.")
            return redirect("editar_usuario", user_id=user_id)

        username_norm = " ".join(username.split()).lower()
        existe_username = Usuario.objects.filter(username_norm=username_norm).exclude(id=usuario.id).exists()
        if existe_username:
            messages.error(request, "Este usuario ya está registrado.")
            return redirect("editar_usuario", user_id=user_id)

        existe_email = Usuario.objects.filter(email__iexact=email).exclude(id=usuario.id).exists()
        if existe_email:
            messages.error(request, "Este correo electrónico ya está registrado.")
            return redirect("editar_usuario", user_id=user_id)

        if telefono:
            if not telefono.isdigit():
                messages.error(request, "El teléfono debe contener solo números.")
                return redirect("editar_usuario", user_id=user_id)

            if len(telefono) != 10:
                messages.error(request, "El teléfono debe tener 10 dígitos.")
                return redirect("editar_usuario", user_id=user_id)

        if direccion and len(direccion) < 10:
            messages.error(request, "La dirección debe tener al menos 10 caracteres.")
            return redirect("editar_usuario", user_id=user_id)

        if genero not in ["M", "F", "O", ""]:
            messages.error(request, "El género seleccionado no es válido.")
            return redirect("editar_usuario", user_id=user_id)

        fecha_nacimiento_value = None
        if fecha_nacimiento:
            try:
                fecha_nacimiento_value = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
                hoy = timezone.localdate()

                if fecha_nacimiento_value > hoy:
                    messages.error(request, "La fecha de nacimiento no puede estar en el futuro.")
                    return redirect("editar_usuario", user_id=user_id)

                if fecha_nacimiento_value.year < 1900:
                    messages.error(request, "El año de nacimiento no puede ser menor a 1900.")
                    return redirect("editar_usuario", user_id=user_id)

            except ValueError:
                messages.error(request, "La fecha de nacimiento no es válida.")
                return redirect("editar_usuario", user_id=user_id)

        usuario.username = username
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.email = email
        usuario.telefono = telefono or None
        usuario.direccion = direccion or None
        usuario.genero = genero or None
        usuario.fecha_nacimiento = fecha_nacimiento_value
        usuario.is_active = is_active
        usuario.save()

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("usuario_detalle", user_id=usuario.id)

    return render(request, "gestion_asociacion/editar_usuario.html", {
        "usuario_obj": usuario,
        "user_role": user_role,
    })


@login_required
@admin_only
def eliminar_usuario(request, user_id: int):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("gestion")

    usuario = Usuario.objects.filter(id=user_id).first()
    if not usuario:
        messages.warning(request, "El usuario ya no existe o fue eliminado.")
        return redirect("gestion")

    if usuario.id == request.user.id:
        messages.error(request, "No puedes eliminar tu propio usuario.")
        return redirect("usuario_detalle", user_id=user_id)

    if getattr(usuario, "rol", "") == "Dios":
        messages.error(request, "No puedes eliminar a un usuario con rol Dios.")
        return redirect("usuario_detalle", user_id=user_id)

    if getattr(usuario, "rol", "") == "Administrador" and getattr(request.user, "rol", "") != "Dios":
        messages.error(request, "Solo un usuario con rol Dios puede eliminar administradores.")
        return redirect("usuario_detalle", user_id=user_id)

    if getattr(request.user, "rol", "") == "Administrador" and getattr(usuario, "rol", "") != "Miembro":
        messages.error(request, "Solo puedes eliminar usuarios con rol Miembro.")
        return redirect("usuario_detalle", user_id=user_id)

    usuario.delete()
    messages.success(request, "Usuario eliminado correctamente.")
    return redirect("gestion")

# ============================================================
# Comunicación (Miembro / Admin)
# ============================================================
@login_required
def comunicacion_interna(request):
    if _es_admin(request.user):
        return redirect("comunicacion_admin")

    recibidos = _mensajes_recibidos(request.user)
    enviados = _mensajes_enviados(request.user)
    asunto_valor = request.GET.get("asunto", "")
    destinatario_id_seleccionado = request.GET.get("destinatario_id", "")

    admins = Usuario.objects.filter(
        rol__in=["Administrador", "Dios"],
        is_active=True
    ).order_by("username")

    no_leidos = Mensaje.objects.filter(
        destinatario=request.user,
        leido=False,
        en_papelera=False
    ).count()

    papelera_count = Mensaje.objects.filter(
        en_papelera=True
    ).filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).count()

    context = {
        "recibidos": recibidos,
        "enviados": enviados,
        "admins": admins,
        "form": MensajeForm(),
        "no_leidos": no_leidos,
        "papelera_count": papelera_count,
        "asunto_valor": asunto_valor,
        "destinatario_id_seleccionado": destinatario_id_seleccionado,
    }

    return render(request, "gestion_asociacion/comunicacion_interna.html", context)


@login_required
@admin_only
def comunicacion_admin(request):
    recibidos = _mensajes_recibidos(request.user)
    enviados = _mensajes_enviados(request.user)

    miembros = Usuario.objects.filter(
        rol="Miembro",
        is_active=True
    ).order_by("username")

    no_leidos = Mensaje.objects.filter(
        destinatario=request.user,
        leido=False,
        en_papelera=False
    ).count()

    papelera_count = Mensaje.objects.filter(
        en_papelera=True
    ).filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).count()

    context = {
        "recibidos": recibidos,
        "enviados": enviados,
        "miembros": miembros,
        "form": MensajeForm(),
        "no_leidos": no_leidos,
        "papelera_count": papelera_count,
    }

    return render(request, "gestion_asociacion/comunicacion_admin.html", context)


@login_required
def ver_mensaje(request, mensaje_id: int):
    msg = Mensaje.objects.select_related(
        "remitente",
        "destinatario"
    ).filter(id=mensaje_id).first()

    if not msg:
        messages.error(request, "Mensaje no encontrado.")
        return redirect("dashboard")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "No tienes permiso para ver este mensaje.")
        return redirect("dashboard")

    if msg.destinatario_id == request.user.id and not msg.leido:
        Mensaje.objects.filter(id=msg.id, leido=False).update(leido=True)
        msg.leido = True

    volver = request.GET.get("volver")

    if volver == "papelera":
        back_url = "papelera"
    else:
        back_url = "comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna"

    return render(request, "gestion_asociacion/ver_mensaje.html", {
        "msg": msg,
        "back_url": back_url,
        "es_admin": _es_admin(request.user),
    })


@login_required
def enviar_mensaje_miembro(request):
    if _es_admin(request.user):
        return redirect("comunicacion_admin")

    if request.method != "POST":
        return redirect("comunicacion_interna")

    destinatario_id = request.POST.get("destinatario_id")

    destinatario = Usuario.objects.filter(
        id=destinatario_id,
        rol__in=["Administrador", "Dios"],
        is_active=True
    ).first()

    recibidos = _mensajes_recibidos(request.user)
    enviados = _mensajes_enviados(request.user)
    admins = Usuario.objects.filter(
        rol__in=["Administrador", "Dios"],
        is_active=True
    ).order_by("username")

    no_leidos = Mensaje.objects.filter(
        destinatario=request.user,
        leido=False,
        en_papelera=False
    ).count()

    papelera_count = Mensaje.objects.filter(
        en_papelera=True
    ).filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).count()

    form = MensajeForm(request.POST, request.FILES)

    if not destinatario:
        form.add_error(None, "Destinatario inválido. Solo puedes enviar a administradores o Dios.")

    if not form.is_valid() or not destinatario:
        return render(request, "gestion_asociacion/comunicacion_interna.html", {
        "recibidos": recibidos,
        "enviados": enviados,
        "admins": admins,
        "form": form,
        "no_leidos": no_leidos,
        "papelera_count": papelera_count,
        "destinatario_id_seleccionado": destinatario_id,
    })

    with transaction.atomic():
        msg = form.save(commit=False)
        msg.remitente = request.user
        msg.destinatario = destinatario
        msg.save()

    messages.success(request, "Mensaje enviado correctamente.")
    return redirect("comunicacion_interna")

@login_required
@admin_only
def enviar_mensaje_admin(request):
    if request.method != "POST":
        return redirect("comunicacion_admin")

    destinatario_id = request.POST.get("destinatario_id")

    destinatario = Usuario.objects.filter(
        id=destinatario_id,
        rol="Miembro",
        is_active=True
    ).first()

    if not destinatario:
        messages.error(request, "Destinatario inválido. Debe ser un miembro activo.")
        return redirect("comunicacion_admin")

    form = MensajeForm(request.POST, request.FILES)

    if not form.is_valid():
        for field, errs in form.errors.items():
            for err in errs:
                messages.error(request, f"{field}: {err}")
        return redirect("comunicacion_admin")

    with transaction.atomic():
        msg = form.save(commit=False)
        msg.remitente = request.user
        msg.destinatario = destinatario
        msg.save()

    messages.success(request, "Mensaje enviado correctamente.")
    return redirect("comunicacion_admin")


# ============================================================
# Papelera (Comunicación)
# ============================================================
@login_required
def papelera(request):
    qs = (
        Mensaje.objects.filter(en_papelera=True)
        .select_related("remitente", "destinatario")
        .order_by("-creado_en")
    ).filter(Q(remitente=request.user) | Q(destinatario=request.user))

    recibidos = qs.filter(destinatario=request.user)
    enviados = qs.filter(remitente=request.user)

    total_papelera = recibidos.count() + enviados.count()

    return render(request, "gestion_asociacion/papelera.html", {
        "recibidos": recibidos,
        "enviados": enviados,
        "total_papelera": total_papelera,
        "es_admin": _es_admin(request.user),
    })


@login_required
def mover_a_papelera(request, mensaje_id: int):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna")

    msg = Mensaje.objects.filter(id=mensaje_id).first()
    if not msg:
        messages.error(request, "Mensaje no encontrado.")
        return redirect("dashboard")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "No tienes permiso para mover este mensaje.")
        return redirect("dashboard")

    Mensaje.objects.filter(id=msg.id).update(en_papelera=True)
    messages.success(request, "Mensaje movido a la papelera.")
    return redirect("comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna")


@login_required
def restaurar_mensaje(request, mensaje_id: int):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("papelera")

    msg = Mensaje.objects.filter(id=mensaje_id).first()
    if not msg:
        messages.error(request, "Mensaje no encontrado.")
        return redirect("papelera")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "No tienes permiso para restaurar este mensaje.")
        return redirect("dashboard")

    Mensaje.objects.filter(id=msg.id).update(en_papelera=False)
    messages.success(request, "Mensaje restaurado correctamente.")

    if _es_admin(request.user):
        return redirect("comunicacion_admin")

    return redirect("comunicacion_interna")


@login_required
def eliminar_definitivo(request, mensaje_id: int):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("papelera")

    msg = Mensaje.objects.filter(id=mensaje_id).first()
    if not msg:
        messages.error(request, "Mensaje no encontrado.")
        return redirect("papelera")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "No tienes permiso para eliminar este mensaje.")
        return redirect("dashboard")

    if not getattr(msg, "en_papelera", False):
        messages.error(request, "Primero debes moverlo a papelera.")
        return redirect("comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna")

    if msg.archivo:
        try:
            msg.archivo.delete(save=False)
        except Exception:
            pass

    msg.delete()
    messages.success(request, "Mensaje eliminado definitivamente.")

    tab = request.POST.get("tab", "recibidos")
    return redirect(f"{reverse('papelera')}?tab={tab}")


@login_required
@admin_only
def control(request):
    hoy = timezone.localdate()

    fecha_inicio_str = request.GET.get("fecha_inicio") or hoy.strftime("%Y-%m-%d")
    fecha_fin_str = request.GET.get("fecha_fin") or hoy.strftime("%Y-%m-%d")

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    except ValueError:
        fecha_inicio = hoy

    try:
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
    except ValueError:
        fecha_fin = hoy

    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    asistencias_qs = (
        Asistencia.objects
        .select_related("usuario")
        .filter(fecha__range=(fecha_inicio, fecha_fin))
        .order_by("-fecha", "usuario__username")
    )

    config_asistencia = obtener_configuracion_asistencia()
    hora_limite_retraso = config_asistencia.hora_limite_retardo()
    hora_limite_extraordinario = config_asistencia.hora_limite_extraordinario

    registros = []

    for asistencia in asistencias_qs:
        if not asistencia.hora_entrada:
            estado = "Sin entrada"
            badge = "secondary"

        elif asistencia.estado == "salida_automatica":
            estado = "Salida automática"
            badge = "info"

        elif asistencia.hora_entrada and not asistencia.hora_salida:
            if asistencia.hora_entrada >= hora_limite_extraordinario:
                estado = "Salida pendiente fuera de horario"
                badge = "primary"
            else:
                estado = "Pendiente salida"
                badge = "warning"

        elif asistencia.hora_entrada >= hora_limite_extraordinario:
            estado = "Asistencia fuera de horario"
            badge = "primary"

        elif asistencia.hora_entrada > hora_limite_retraso:
            estado = "Asistencia completa con retardo"
            badge = "danger"

        elif asistencia.hora_salida:
            estado = "Asistencia completa"
            badge = "success"

        else:
            estado = "Sin estado"
            badge = "secondary"

        registros.append({
            "obj": asistencia,
            "estado": estado,
            "badge": badge,
        })

    dias_trabajados = asistencias_qs.filter(
        hora_entrada__isnull=False
    ).count()

    dias_con_retrasos = asistencias_qs.filter(
        hora_entrada__gt=hora_limite_retraso,
        hora_entrada__lt=hora_limite_extraordinario
    ).count()

    usuarios_activos = Usuario.objects.filter(
        is_active=True,
        rol="Miembro"
    )

    total_miembros_activos = usuarios_activos.count()

    usuarios_con_registro = (
        asistencias_qs
        .exclude(usuario__isnull=True)
        .values_list("usuario_id", flat=True)
        .distinct()
        .count()
    )

    usuarios_sin_registro = max(
        total_miembros_activos - usuarios_con_registro,
        0
    )

    context = {
        "registros": registros,
        "fecha_inicio_valor": fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin_valor": fecha_fin.strftime("%Y-%m-%d"),
        "total_registros": asistencias_qs.count(),
        "dias_trabajados": dias_trabajados,
        "dias_con_retrasos": dias_con_retrasos,
        "usuarios_sin_registro": usuarios_sin_registro,
        "total_miembros_activos": total_miembros_activos,
        "hora_limite_retraso_texto": hora_limite_retraso.strftime("%I:%M %p"),
        "config_asistencia": config_asistencia,
    }

    return render(request, "gestion_asociacion/control.html", context)

@login_required
@admin_only
def gestion_cap(request):
    form_capacitacion = CapacitacionForm()
    form_asignacion = CapacitacionAsignadaForm()

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "crear_capacitacion":
            form_capacitacion = CapacitacionForm(request.POST)

            if form_capacitacion.is_valid():
                capacitacion = form_capacitacion.save(commit=False)
                capacitacion.creado_por = request.user
                capacitacion.save()

                messages.success(request, "Capacitación creada correctamente.")
                return redirect("gestion_cap")

            messages.error(request, "Revisa los datos de la capacitación.")

        elif accion == "asignar_capacitacion":
            form_asignacion = CapacitacionAsignadaForm(request.POST)

            if form_asignacion.is_valid():
                capacitacion = form_asignacion.cleaned_data["capacitacion"]
                usuarios = form_asignacion.cleaned_data["usuarios"]
                fecha_limite = form_asignacion.cleaned_data.get("fecha_limite")
                fecha_vencimiento = form_asignacion.cleaned_data.get("fecha_vencimiento")
                observaciones = form_asignacion.cleaned_data.get("observaciones")

                creadas = 0
                existentes = 0
            
                if fecha_limite and fecha_vencimiento and fecha_limite > fecha_vencimiento:
                    messages.error(request, "La fecha límite no puede ser mayor que la fecha de vencimiento.")
                    return redirect("gestion_cap")

                with transaction.atomic():
                    for usuario in usuarios:
                        obj, created = CapacitacionAsignada.objects.get_or_create(
                            capacitacion=capacitacion,
                            usuario=usuario,
                            defaults={
                                "fecha_limite": fecha_limite,
                                "fecha_vencimiento": fecha_vencimiento,
                                "observaciones": observaciones,
                                "estado": "pendiente",
                            }
                        )

                        if created:
                            creadas += 1
                        else:
                            existentes += 1

                if creadas:
                    messages.success(request, f"Capacitación asignada correctamente a {creadas} usuario(s).")

                if existentes:
                    messages.warning(request, f"{existentes} usuario(s) ya tenían asignada esta capacitación.")

                return redirect("gestion_cap")

            messages.error(request, "Revisa los datos de la asignación.")

    capacitaciones = (
        Capacitacion.objects
        .all()
        .order_by("nombre")
    )

    asignaciones = (
        CapacitacionAsignada.objects
        .select_related("capacitacion", "usuario")
        .order_by("-fecha_asignacion")[:20]
    )

    total_capacitaciones = capacitaciones.count()
    capacitaciones_activas = capacitaciones.filter(estado="activa").count()
    total_asignaciones = CapacitacionAsignada.objects.count()
    pendientes = CapacitacionAsignada.objects.filter(estado="pendiente").count()
    aprobadas = CapacitacionAsignada.objects.filter(estado="aprobada").count()
    vencidas = sum(1 for a in CapacitacionAsignada.objects.all() if a.esta_vencida)

    context = {
        "capacitaciones": capacitaciones,
        "asignaciones": asignaciones,
        "form_capacitacion": form_capacitacion,
        "form_asignacion": form_asignacion,
        "total_capacitaciones": total_capacitaciones,
        "capacitaciones_activas": capacitaciones_activas,
        "total_asignaciones": total_asignaciones,
        "pendientes": pendientes,
        "aprobadas": aprobadas,
        "vencidas": vencidas,
    }

    return render(request, "gestion_asociacion/gestion_cap.html", context)

@login_required
@admin_only
def editar_capacitacion(request, capacitacion_id):
    capacitacion = Capacitacion.objects.filter(id=capacitacion_id).first()

    if not capacitacion:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": False,
                "mensaje": "Capacitación no encontrada."
            }, status=404)

        messages.error(request, "Capacitación no encontrada.")
        return redirect("gestion_cap")

    if request.method != "POST":
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": False,
                "mensaje": "Método no permitido."
            }, status=405)

        messages.error(request, "Método no permitido.")
        return redirect("gestion_cap")

    form = CapacitacionForm(request.POST, instance=capacitacion)

    if form.is_valid():
        capacitacion = form.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": True,
                "mensaje": "Capacitación actualizada correctamente.",
                "capacitacion": {
                    "id": capacitacion.id,
                    "nombre": capacitacion.nombre,
                    "modalidad": capacitacion.modalidad,
                    "duracion_horas": capacitacion.duracion_horas,
                    "estado": capacitacion.estado,
                    "estado_visual": "Activa" if capacitacion.estado == "activa" else "Inactiva",
                    "estado_badge": "success" if capacitacion.estado == "activa" else "secondary",
                }
            })

        messages.success(request, "Capacitación actualizada correctamente.")
        return redirect("gestion_cap")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": False,
            "mensaje": "Revisa los datos de la capacitación."
        }, status=400)

    messages.error(request, "Revisa los datos de la capacitación.")
    return redirect("gestion_cap")


@login_required
@admin_only
def eliminar_capacitacion(request, capacitacion_id):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("gestion_cap")

    capacitacion = Capacitacion.objects.filter(id=capacitacion_id).first()

    if not capacitacion:
        messages.error(request, "Capacitación no encontrada.")
        return redirect("gestion_cap")

    capacitacion.delete()
    messages.success(request, "Capacitación eliminada correctamente.")
    return redirect("gestion_cap")

@login_required
@admin_only
def editar_asignacion_capacitacion(request, asignacion_id):
    asignacion = (
        CapacitacionAsignada.objects
        .select_related("capacitacion", "usuario")
        .filter(id=asignacion_id)
        .first()
    )

    if not asignacion:
        messages.error(request, "Asignación no encontrada.")
        return redirect("gestion_cap")

    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("gestion_cap")

    estado = request.POST.get("estado")
    fecha_limite = request.POST.get("fecha_limite") or None
    fecha_vencimiento = request.POST.get("fecha_vencimiento") or None
    observaciones = request.POST.get("observaciones") or ""

    estados_validos = ["pendiente", "en_proceso", "aprobada", "vencida", "cancelada"]

    if estado not in estados_validos:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": False,
                "mensaje": "Estado no válido."
            }, status=400)

        messages.error(request, "Estado no válido.")
        return redirect("gestion_cap")

    if fecha_limite and fecha_vencimiento and fecha_limite > fecha_vencimiento:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": False,
                "mensaje": "La fecha límite no puede ser mayor que la fecha de vencimiento."
            }, status=400)

        messages.error(request, "La fecha límite no puede ser mayor que la fecha de vencimiento.")
        return redirect("gestion_cap")

    asignacion.estado = estado
    asignacion.fecha_limite = fecha_limite
    asignacion.fecha_vencimiento = fecha_vencimiento
    asignacion.observaciones = observaciones
    asignacion.save(update_fields=[
        "estado",
        "fecha_limite",
        "fecha_vencimiento",
        "observaciones",
    ])

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "mensaje": "Asignación actualizada correctamente."
        })

    messages.success(request, "Asignación actualizada correctamente.")
    return redirect("gestion_cap")


@login_required
@admin_only
def eliminar_asignacion_capacitacion(request, asignacion_id):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("gestion_cap")

    asignacion = CapacitacionAsignada.objects.filter(id=asignacion_id).first()

    if not asignacion:
        messages.error(request, "Asignación no encontrada.")
        return redirect("gestion_cap")

    asignacion.delete()
    messages.success(request, "Asignación eliminada correctamente.")
    return redirect("gestion_cap")


@login_required
@admin_only
def nomina(request):
    return render(request, "gestion_asociacion/nomina.html")


@login_required
@admin_only
def evaluacion_desem(request):
    return render(request, "gestion_asociacion/evaluacion_desem.html")


@login_required
@admin_only
def add_personal(request):
    if request.method == "POST":
        Personal.objects.create(
            nombre=request.POST["nombre"],
            email=request.POST["email"],
            telefono=request.POST.get("telefono", ""),
            departamento=request.POST["departamento"],
            comentarios=request.POST.get("comentarios", ""),
        )
        messages.success(request, "Nuevo personal añadido correctamente.")
        return redirect("dashboard")

    return render(request, "gestion_asociacion/add_personal.html")


@login_required
@admin_only
def add_event(request):
    if request.method == "POST":
        Evento.objects.create(
            titulo=request.POST["titulo"],
            fecha=request.POST["fecha"],
            descripcion=request.POST["descripcion"],
        )
        messages.success(request, "Nuevo evento creado correctamente.")
        return redirect("dashboard")

    return render(request, "gestion_asociacion/add_event.html")


# ============================================================
# AJAX / utilidades
# ============================================================
def verificar_usuario(request):
    username = " ".join((request.GET.get("username") or "").strip().split()).lower()
    email = (request.GET.get("email") or "").strip().lower()

    exists = False
    if username:
        exists = exists or User.objects.filter(username_norm=username).exists()
    if email:
        exists = exists or User.objects.filter(email__iexact=email).exists()

    return JsonResponse({"exists": exists})


# ============================================================
# Promover usuario
# ============================================================
@login_required
@admin_only
def promover_usuario(request, user_id):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("gestion")

    next_url = request.POST.get("next") or ""
    if not next_url.startswith("/"):
        next_url = ""

    try:
        with transaction.atomic():
            usuario = Usuario.objects.select_for_update().get(id=user_id)

            # ❌ No modificar su propio rol desde aquí
            if usuario.id == request.user.id:
                messages.error(request, "No puedes modificar tu propio rol desde aquí.")
                return redirect(next_url or "gestion")

            # ❌ No modificar superusuarios
            if getattr(usuario, "is_superuser", False):
                messages.error(request, "No puedes modificar el rol de un superusuario.")
                return redirect(next_url or "gestion")

            # ❌ No modificar usuarios Dios desde esta vista
            if getattr(usuario, "rol", "") == "Dios":
                messages.error(request, "No puedes modificar el rol de un usuario Dios desde aquí.")
                return redirect(next_url or "gestion")

            # ✅ Solo promover miembros
            if getattr(usuario, "rol", "") != "Miembro":
                messages.error(request, "Solo puedes promover usuarios con rol Miembro.")
                return redirect(next_url or "gestion")

            usuario.rol = "Administrador"
            usuario.save(update_fields=["rol"])

        messages.success(request, f"{usuario.username} fue promovido a Administrador.")
        return redirect(next_url or "gestion")

    except Usuario.DoesNotExist:
        messages.error(request, " Usuario no encontrado.")
        return redirect(next_url or "gestion")
    
@login_required
@admin_only
def cambiar_rol_usuario(request, user_id):
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("gestion")

    user_role = getattr(request.user, "rol", "")

    if user_role != "Dios":
        messages.error(request, "Solo un usuario con rol Dios puede cambiar roles.")
        return redirect("gestion")

    usuario = Usuario.objects.filter(id=user_id).first()
    if not usuario:
        messages.error(request, "Usuario no encontrado.")
        return redirect("gestion")

    if usuario.id == request.user.id:
        messages.error(request, "No puedes modificar tu propio rol desde esta vista.")
        return redirect("usuario_detalle", user_id=user_id)

    if getattr(usuario, "rol", "") == "Dios":
        messages.error(request, "No puedes modificar el rol de un usuario Dios.")
        return redirect("usuario_detalle", user_id=user_id)

    nuevo_rol = (request.POST.get("nuevo_rol") or "").strip()

    if nuevo_rol not in ["Administrador", "Miembro"]:
        messages.error(request, "El nuevo rol no es válido.")
        return redirect("usuario_detalle", user_id=user_id)

    if usuario.rol == nuevo_rol:
        messages.warning(request, "El usuario ya tiene ese rol.")
        return redirect("usuario_detalle", user_id=user_id)

    usuario.rol = nuevo_rol

    if nuevo_rol == "Administrador":
        usuario.is_staff = True
        usuario.is_superuser = False

    elif nuevo_rol == "Miembro":
        usuario.is_staff = False
        usuario.is_superuser = False

    usuario.save(update_fields=["rol", "is_staff", "is_superuser"])

    messages.success(request, f"El rol de {usuario.username} fue actualizado a {nuevo_rol}.")
    return redirect("usuario_detalle", user_id=user_id)