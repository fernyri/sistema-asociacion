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

from .decorators import admin_only
from .forms import MensajeForm, RegistroForm
from .models import (
    Asistencia,
    AttendanceSummary,
    BitacoraAcceso,
    Evento,
    Mensaje,
    Notification,
    Personal,
    Usuario,
)

User = get_user_model()


# ============================================================
# Helpers
# ============================================================
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


def login_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password")

        user_obj = Usuario.objects.filter(email__iexact=email).first()

        if user_obj is None:
            messages.error(request, "El correo no existe.", extra_tags="email_error")
            return redirect("login")

        if not user_obj.is_active:
            messages.error(
                request,
                "Tu cuenta no ha sido verificada. Revisa tu correo o solicita un nuevo enlace.",
                extra_tags="email_error"
            )
            return redirect("login")

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)

        messages.error(request, "Contraseña incorrecta.", extra_tags="password_error")
        return redirect("login")

    return render(request, "gestion_asociacion/primer_login.html")

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect("login")


# ============================================================
# Dashboard
# ============================================================
@login_required
def dashboard(request):
    rol_usuario = getattr(request.user, "rol", "No definido")

    if rol_usuario == "Miembro":
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

        mensajes_no_leidos = Mensaje.objects.filter(
            destinatario=request.user,
            leido=False,
            en_papelera=False
        ).count()

        context = {
            "user": request.user,
            "user_role": rol_usuario,
            "ultimo_acceso": ultimo_acceso,
            "sesiones_activas": sesiones_activas,
            "total_sesiones_activas": sesiones_activas.count(),
            "ultimas_asistencias": ultimas_asistencias,
            "mensajes_no_leidos": mensajes_no_leidos,
        }
        return render(request, "gestion_asociacion/dashboard_miembro.html", context)

    attendance_summary = AttendanceSummary.objects.order_by("-date").first()
    attendance_records = (
        Asistencia.objects
        .select_related("usuario")
        .order_by("-fecha", "-hora_entrada")[:10]
    )
    notifications = Notification.objects.all().order_by("-created_at")[:5]

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
        "attendance_summary": attendance_summary,
        "attendance_records": attendance_records,
        "ultimos_accesos": ultimos_accesos,
        "usuarios_conectados": usuarios_conectados,
        "total_usuarios_conectados": usuarios_conectados.count(),
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
        messages.warning(request, "El usuario no existe (posiblemente fue eliminado).")
        return redirect("gestion")

    user_role = getattr(request.user, "rol", "")

    # ❌ Nadie se edita a sí mismo desde esta vista
    if usuario.id == request.user.id:
        messages.error(request, "No puedes editar tu propio usuario desde esta vista.")
        return redirect("usuario_detalle", user_id=user_id)

    # ❌ Nadie edita a un Dios desde esta vista
    if getattr(usuario, "rol", "") == "Dios":
        messages.error(request, "No puedes editar a un usuario con rol Dios desde esta vista.")
        return redirect("usuario_detalle", user_id=user_id)

    # ❌ Administrador solo edita Miembros
    if user_role == "Administrador" and getattr(usuario, "rol", "") != "Miembro":
        messages.error(request, "Solo puedes editar usuarios con rol Miembro.")
        return redirect("usuario_detalle", user_id=user_id)

    # ❌ Solo Dios puede editar Administradores
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

        # Validaciones básicas
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

        # Validar username único
        username_norm = " ".join(username.split()).lower()
        existe_username = Usuario.objects.filter(username_norm=username_norm).exclude(id=usuario.id).exists()
        if existe_username:
            messages.error(request, "Este usuario ya está registrado.")
            return redirect("editar_usuario", user_id=user_id)

        # Validar email único
        existe_email = Usuario.objects.filter(email__iexact=email).exclude(id=usuario.id).exists()
        if existe_email:
            messages.error(request, "Este correo electrónico ya está registrado.")
            return redirect("editar_usuario", user_id=user_id)

        # Validar teléfono
        if telefono:
            if not telefono.isdigit():
                messages.error(request, "El teléfono debe contener solo números.")
                return redirect("editar_usuario", user_id=user_id)
            if len(telefono) < 10 or len(telefono) > 10:
                messages.error(request, "El teléfono debe tener 10 dígitos.")
                return redirect("editar_usuario", user_id=user_id)

        # Validar dirección
        if direccion and len(direccion) < 10:
            messages.error(request, "La dirección debe tener al menos 10 caracteres.")
            return redirect("editar_usuario", user_id=user_id)

        # Validar género
        if genero not in ["M", "F", "O", ""]:
            messages.error(request, "El género seleccionado no es válido.")
            return redirect("editar_usuario", user_id=user_id)

        # Validar fecha
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

    # ❌ No puede eliminarse a sí mismo
    if usuario.id == request.user.id:
        messages.error(request, "No puedes eliminar tu propio usuario.")
        return redirect("usuario_detalle", user_id=user_id)

    # ❌ No puede eliminar superusuarios
    if getattr(usuario, "is_superuser", False):
        messages.error(request, "No puedes eliminar un superusuario.")
        return redirect("usuario_detalle", user_id=user_id)

    # ❌ Nadie elimina a un usuario con rol Dios desde aquí
    if getattr(usuario, "rol", "") == "Dios":
        messages.error(request, "No puedes eliminar a un usuario con rol Dios.")
        return redirect("usuario_detalle", user_id=user_id)

    # ❌ Solo Dios puede eliminar administradores
    if getattr(usuario, "rol", "") == "Administrador" and getattr(request.user, "rol", "") != "Dios":
        messages.error(request, "Solo un usuario con rol superuser puede eliminar administradores.")
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
    admins = Usuario.objects.filter(rol="Administrador").order_by("username")

    context = {
        "recibidos": recibidos,
        "enviados": enviados,
        "admins": admins,
        "form": MensajeForm(),
    }
    return render(request, "gestion_asociacion/comunicacion_interna.html", context)


@login_required
@admin_only
def comunicacion_admin(request):
    recibidos = _mensajes_recibidos(request.user)
    enviados = _mensajes_enviados(request.user)
    miembros = Usuario.objects.filter(rol="Miembro").order_by("username")

    context = {
        "recibidos": recibidos,
        "enviados": enviados,
        "miembros": miembros,
        "form": MensajeForm(),
    }
    return render(request, "gestion_asociacion/comunicacion_admin.html", context)


@login_required
def ver_mensaje(request, mensaje_id: int):
    msg = Mensaje.objects.select_related("remitente", "destinatario").filter(id=mensaje_id).first()
    if not msg:
        messages.error(request, " Mensaje no encontrado.")
        return redirect("dashboard")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, " No tienes permiso para ver este mensaje.")
        return redirect("dashboard")

    if msg.destinatario_id == request.user.id and not msg.leido:
        Mensaje.objects.filter(id=msg.id, leido=False).update(leido=True)

    back_url = "comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna"
    return render(request, "gestion_asociacion/ver_mensaje.html", {"msg": msg, "back_url": back_url})


@login_required
def enviar_mensaje_miembro(request):
    if _es_admin(request.user):
        return redirect("comunicacion_admin")

    if request.method != "POST":
        return redirect("comunicacion_interna")

    destinatario_id = request.POST.get("destinatario_id")
    destinatario = Usuario.objects.filter(id=destinatario_id, rol="Administrador").first()

    if not destinatario:
        messages.error(request, "Destinatario inválido. Solo puedes enviar a administradores.")
        return redirect("comunicacion_interna")

    form = MensajeForm(request.POST, request.FILES)
    if not form.is_valid():
        for field, errs in form.errors.items():
            for err in errs:
                messages.error(request, f"{field}: {err}")
        return redirect("comunicacion_interna")

    with transaction.atomic():
        msg = form.save(commit=False)
        msg.remitente = request.user
        msg.destinatario = destinatario
        msg.save()

    messages.success(request, " Mensaje enviado al administrador.")
    return redirect("comunicacion_interna")


@login_required
@admin_only
def enviar_mensaje_admin(request):
    if request.method != "POST":
        return redirect("comunicacion_admin")

    destinatario_id = request.POST.get("destinatario_id")
    destinatario = Usuario.objects.filter(id=destinatario_id, rol="Miembro").first()

    if not destinatario:
        messages.error(request, "Destinatario inválido (debe ser miembro).")
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

    messages.success(request, "Mensaje enviado al miembro.")
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

    return render(request, "gestion_asociacion/papelera.html", {
        "recibidos": recibidos,
        "enviados": enviados,
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
    messages.success(request, "Mensaje restaurado.")

    tab = request.POST.get("tab", "recibidos")
    return redirect(f"{reverse('papelera')}?tab={tab}")


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


# ============================================================
# Secciones Admin
# ============================================================
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

    hora_limite_retraso = time(9, 15)

    registros = []
    for asistencia in asistencias_qs:
        if not asistencia.hora_entrada:
            estado = "Sin entrada"
            badge = "secondary"
        elif asistencia.hora_entrada > hora_limite_retraso:
            estado = "Retardo"
            badge = "warning"
        elif asistencia.hora_salida:
            estado = "Asistencia completa"
            badge = "success"
        else:
            estado = "Pendiente salida"
            badge = "info"

        registros.append({
            "obj": asistencia,
            "estado": estado,
            "badge": badge,
        })

    dias_trabajados = asistencias_qs.filter(hora_entrada__isnull=False).count()
    dias_con_retrasos = asistencias_qs.filter(hora_entrada__gt=hora_limite_retraso).count()

    usuarios_activos = Usuario.objects.filter(is_active=True, rol="Miembro")
    total_miembros_activos = usuarios_activos.count()

    usuarios_con_registro = (
        asistencias_qs
        .exclude(usuario__isnull=True)
        .values_list("usuario_id", flat=True)
        .distinct()
        .count()
    )

    usuarios_sin_registro = max(total_miembros_activos - usuarios_con_registro, 0)

    context = {
        "registros": registros,
        "fecha_inicio_valor": fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin_valor": fecha_fin.strftime("%Y-%m-%d"),
        "total_registros": asistencias_qs.count(),
        "dias_trabajados": dias_trabajados,
        "dias_con_retrasos": dias_con_retrasos,
        "usuarios_sin_registro": usuarios_sin_registro,
        "total_miembros_activos": total_miembros_activos,
        "hora_limite_retraso_texto": "09:15 AM",
    }
    return render(request, "gestion_asociacion/control.html", context)


@login_required
@admin_only
def gestion_cap(request):
    return render(request, "gestion_asociacion/gestion_cap.html")


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

    # Mantener banderas de acceso del staff
    if nuevo_rol == "Administrador":
        usuario.is_staff = True
    elif nuevo_rol == "Miembro":
        usuario.is_staff = False

    usuario.save(update_fields=["rol", "is_staff"])

    messages.success(request, f"El rol de {usuario.username} fue actualizado a {nuevo_rol}.")
    return redirect("usuario_detalle", user_id=user_id)