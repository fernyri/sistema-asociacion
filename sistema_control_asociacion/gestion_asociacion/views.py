# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout as auth_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from datetime import datetime, time

from django.contrib.sessions.models import Session
from django.utils import timezone

from .forms import RegistroForm, MensajeForm
from .models import Notification, AttendanceSummary, Personal, Evento, Usuario, Asistencia, Mensaje
from .decorators import admin_only

# ✅ User model activo (tu Usuario personalizado)
User = get_user_model()


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
        # ✅ Primero Django guarda la nueva contraseña
        response = super().form_valid(form)

        # ✅ Usuario al que se le cambió la contraseña
        user = form.user

        # ✅ Invalidar TODAS las sesiones activas de ese usuario
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
# Helpers
# ============================================================
def _es_admin(u: Usuario) -> bool:
    return getattr(u, "rol", "") == "Administrador"


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


# ============================================================
# Auth / Login / Registro
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
                    form.save()

                messages.success(request, "✅ Usuario registrado correctamente.")
                return redirect("login")

            except IntegrityError:
                messages.error(request, "⚠️ El usuario o correo ya están registrados.")

        for field, errs in form.errors.items():
            for err in errs:
                messages.error(request, f"{field}: {err}")
    else:
        form = RegistroForm()

    return render(request, "gestion_asociacion/registro.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password")

        user_obj = Usuario.objects.filter(email__iexact=email).first()
        if user_obj is None:
            messages.error(request, "⚠️ El correo no existe.", extra_tags="email_error")
            return redirect("login")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)

        messages.error(request, "❌ Contraseña incorrecta.", extra_tags="password_error")
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
        return redirect("comunicacion_interna")

    context = {
        "notifications": Notification.objects.all().order_by("-created_at")[:5],
        "attendance_summary": AttendanceSummary.objects.last(),
        "attendance_records": Asistencia.objects.all().order_by("-fecha")[:10],
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
    # ✅ muestra Miembros + Administradores (excluye superusuarios)
    miembros = (
        Usuario.objects
        .filter(is_superuser=False)
        .order_by("username")
    )
    return render(request, "gestion_asociacion/gestion.html", {"miembros": miembros})


@login_required
@admin_only
def usuario_detalle(request, user_id: int):
    # ✅ En vez de 404 feo, redirige con mensaje si no existe
    usuario = Usuario.objects.filter(id=user_id).first()
    if not usuario:
        messages.warning(request, "⚠️ El usuario no existe (posiblemente fue eliminado).")
        return redirect("gestion")

    return render(request, "gestion_asociacion/usuario_detalle.html", {
        "usuario_obj": usuario,
    })


@login_required
@admin_only
def eliminar_usuario(request, user_id: int):
    if request.method != "POST":
        messages.error(request, "❌ Método no permitido.")
        return redirect("gestion")

    usuario = Usuario.objects.filter(id=user_id).first()
    if not usuario:
        messages.warning(request, "⚠️ El usuario ya no existe o fue eliminado.")
        return redirect("gestion")

    # 🚫 Evitar que se elimine a sí mismo
    if usuario.id == request.user.id:
        messages.error(request, "⚠️ No puedes eliminar tu propio usuario.")
        return redirect("usuario_detalle", user_id=user_id)

    # 🚫 Evitar eliminar superusuario
    if getattr(usuario, "is_superuser", False):
        messages.error(request, "⚠️ No puedes eliminar un superusuario.")
        return redirect("usuario_detalle", user_id=user_id)

    usuario.delete()
    messages.success(request, "✅ Usuario eliminado correctamente.")

    # ✅ IMPORTANTE: tras eliminar, SIEMPRE regresa a gestión (evita 404 del perfil borrado)
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
        messages.error(request, "❌ Mensaje no encontrado.")
        return redirect("dashboard")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "❌ No tienes permiso para ver este mensaje.")
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
        messages.error(request, "⚠️ Destinatario inválido. Solo puedes enviar a administradores.")
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

    messages.success(request, "✅ Mensaje enviado al administrador.")
    return redirect("comunicacion_interna")


@login_required
@admin_only
def enviar_mensaje_admin(request):
    if request.method != "POST":
        return redirect("comunicacion_admin")

    destinatario_id = request.POST.get("destinatario_id")
    destinatario = Usuario.objects.filter(id=destinatario_id, rol="Miembro").first()

    if not destinatario:
        messages.error(request, "⚠️ Destinatario inválido (debe ser miembro).")
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

    messages.success(request, "✅ Mensaje enviado al miembro.")
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
        messages.error(request, "❌ Método no permitido.")
        return redirect("comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna")

    msg = Mensaje.objects.filter(id=mensaje_id).first()
    if not msg:
        messages.error(request, "❌ Mensaje no encontrado.")
        return redirect("dashboard")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "❌ No tienes permiso para mover este mensaje.")
        return redirect("dashboard")

    Mensaje.objects.filter(id=msg.id).update(en_papelera=True)
    messages.success(request, "🗑️ Mensaje movido a la papelera.")
    return redirect("comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna")


@login_required
def restaurar_mensaje(request, mensaje_id: int):
    if request.method != "POST":
        messages.error(request, "❌ Método no permitido.")
        return redirect("papelera")

    msg = Mensaje.objects.filter(id=mensaje_id).first()
    if not msg:
        messages.error(request, "❌ Mensaje no encontrado.")
        return redirect("papelera")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "❌ No tienes permiso para restaurar este mensaje.")
        return redirect("dashboard")

    Mensaje.objects.filter(id=msg.id).update(en_papelera=False)
    messages.success(request, "✅ Mensaje restaurado.")

    tab = request.POST.get("tab", "recibidos")
    return redirect(f"{reverse('papelera')}?tab={tab}")


@login_required
def eliminar_definitivo(request, mensaje_id: int):
    if request.method != "POST":
        messages.error(request, "❌ Método no permitido.")
        return redirect("papelera")

    msg = Mensaje.objects.filter(id=mensaje_id).first()
    if not msg:
        messages.error(request, "❌ Mensaje no encontrado.")
        return redirect("papelera")

    if not _user_puede_ver_mensaje(request.user, msg):
        messages.error(request, "❌ No tienes permiso para eliminar este mensaje.")
        return redirect("dashboard")

    if not getattr(msg, "en_papelera", False):
        messages.error(request, "⚠️ Primero debes moverlo a papelera.")
        return redirect("comunicacion_admin" if _es_admin(request.user) else "comunicacion_interna")

    if msg.archivo:
        try:
            msg.archivo.delete(save=False)
        except Exception:
            pass

    msg.delete()
    messages.success(request, "✅ Mensaje eliminado definitivamente.")

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

    # ✅ Si el usuario mete fechas invertidas, las acomodamos
    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    asistencias_qs = (
        Asistencia.objects
        .select_related("usuario")
        .filter(fecha__range=(fecha_inicio, fecha_fin))
        .order_by("-fecha", "usuario__username")
    )

    # ✅ Hora límite para considerar retardo
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

    # ✅ Resúmenes reales
    dias_trabajados = asistencias_qs.filter(hora_entrada__isnull=False).count()
    dias_con_retrasos = asistencias_qs.filter(hora_entrada__gt=hora_limite_retraso).count()

    # ✅ Sin campo departamento real, usamos miembros activos para calcular "sin registro"
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
        messages.error(request, "❌ Método no permitido.")
        return redirect("gestion")

    next_url = request.POST.get("next") or ""
    if not next_url.startswith("/"):
        next_url = ""

    try:
        with transaction.atomic():
            usuario = Usuario.objects.select_for_update().get(id=user_id)

            if usuario.id == request.user.id:
                messages.error(request, "⚠️ No puedes modificar tu propio rol desde aquí.")
                return redirect(next_url or "gestion")

            if getattr(usuario, "is_superuser", False):
                messages.error(request, "⚠️ No puedes modificar el rol de un superusuario.")
                return redirect(next_url or "gestion")

            if getattr(usuario, "rol", "") != "Miembro":
                messages.error(request, "⚠️ Solo puedes promover usuarios con rol Miembro.")
                return redirect(next_url or "gestion")

            usuario.rol = "Administrador"
            usuario.save(update_fields=["rol"])

        messages.success(request, f"✅ {usuario.username} fue promovido a Administrador.")
        return redirect(next_url or "gestion")

    except Usuario.DoesNotExist:
        messages.error(request, "❌ Usuario no encontrado.")
        return redirect(next_url or "gestion")