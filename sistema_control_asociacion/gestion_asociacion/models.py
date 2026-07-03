from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.functions import Lower
from datetime import time
from django.utils import timezone


# =========================
# Helper: nombre bonito
# =========================
def nombre_bonito(valor: str) -> str:
    """
    Normaliza textos “humanos”:
    - Quita espacios extra
    - Capitaliza palabras
    - Mantiene preposiciones comunes en minúscula (de, la, del, etc.)
    """
    if not valor:
        return ""

    minusculas = {"de", "la", "del", "y", "e", "los", "las"}
    partes = str(valor).strip().split()
    resultado = []

    for p in partes:
        pl = p.lower()
        if pl in minusculas:
            resultado.append(pl)
        else:
            resultado.append(pl.capitalize())

    return " ".join(resultado)


def username_norm_value(v: str) -> str:
    """
    ✅ Normalización real para unicidad (case-insensitive + espacios):
    - strip
    - colapsa espacios
    - lower
    """
    v = " ".join(str(v or "").strip().split())
    return v.lower()


# =========================
# UserManager personalizado
# =========================
class UsuarioManager(BaseUserManager):

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")

        email = (self.normalize_email(email) or "").strip().lower()
        username_clean = " ".join((username or "").strip().split())

        user = self.model(
            username=username_clean,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.username_norm = username_norm_value(username_clean)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # ✅ El superusuario será el nivel más alto del sistema
        extra_fields.setdefault("rol", "Dios")

        return self.create_user(username, email, password, **extra_fields)


# =========================
# Usuario personalizado
# =========================
class Usuario(AbstractUser):

    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico"
    )

    username_norm = models.CharField(
        max_length=150,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Username normalizado",
    )

    telefono = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )

    direccion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Dirección"
    )

    genero = models.CharField(
        max_length=10,
        choices=[
            ("M", "Masculino"),
            ("F", "Femenino"),
            ("O", "Otro")
        ],
        verbose_name="Género",
        blank=True,
        null=True,
    )

    fecha_nacimiento = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de nacimiento"
    )

    rol = models.CharField(
        max_length=50,
        choices=[
            ("Dios", "Dios"),
            ("Administrador", "Administrador"),
            ("Miembro", "Miembro"),
        ],
        verbose_name="Rol",
        default="Miembro",
    )

    objects = UsuarioManager()

    # =========================
    # SAVE NORMALIZADO
    # =========================
    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        self.username = nombre_bonito(self.username)
        self.first_name = nombre_bonito(self.first_name)
        self.last_name = nombre_bonito(self.last_name)
        self.username_norm = username_norm_value(self.username)

        super().save(*args, **kwargs)

    # =========================
    # Helpers de rol
    # =========================
    def is_dios(self):
        return self.rol == "Dios"

    def is_admin(self):
        return self.rol == "Administrador"

    def is_miembro(self):
        return self.rol == "Miembro"

    def __str__(self):
        return (
            f"{self.username} ({self.first_name} {self.last_name})"
            if self.first_name else self.username
        )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="uniq_usuario_email_lower"),
        ]


# =========================
# Asistencia
# =========================
class Asistencia(models.Model):

    ESTADO_CHOICES = [
        ("sin_entrada", "Sin entrada"),
        ("salida_pendiente", "Salida pendiente"),
        ("asistencia_completa", "Asistencia completa"),
        ("salida_automatica", "Salida automática"),
        ("retardo", "Retardo"),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asistencias",
        verbose_name="Usuario",
    )

    fecha = models.DateField(verbose_name="Fecha")

    hora_entrada = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Hora de entrada"
    )

    hora_salida = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Hora de salida"
    )

    estado = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default="sin_entrada",
        db_index=True,
        verbose_name="Estado"
    )

    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observación"
    )

    @property
    def tiene_retardo(self):
        config = ConfiguracionAsistencia.objects.filter(activa=True).first()

        if not config:
            hora_limite_retardo = time(9, 15)
            hora_limite_extraordinario = time(18, 0)
        else:
            hora_limite_retardo = config.hora_limite_retardo()
            hora_limite_extraordinario = config.hora_limite_extraordinario

        return bool(
            self.hora_entrada
            and self.hora_entrada > hora_limite_retardo
            and self.hora_entrada < hora_limite_extraordinario
        )
    
    @property
    def es_extraordinario(self):
        config = ConfiguracionAsistencia.objects.filter(activa=True).first()

        if not config:
            hora_limite_extraordinario = time(18, 0)
        else:
            hora_limite_extraordinario = config.hora_limite_extraordinario

        return bool(self.hora_entrada and self.hora_entrada >= hora_limite_extraordinario)

    @property
    def estado_texto(self):
        if self.estado == "salida_automatica":
            return "Salida automática"

        if not self.hora_entrada:
            return "Sin entrada"

        if self.hora_entrada and not self.hora_salida:
            if self.es_extraordinario:
                return "Salida pendiente fuera de horario"
            return "Salida pendiente"

        if self.es_extraordinario:
            return "Asistencia fuera de horario"

        if self.tiene_retardo:
            return "Asistencia con retardo"

        return "Asistencia completa"
    
    @property
    def estado_calculado(self):
        if self.estado == "salida_automatica":
            return "salida_automatica"

        if not self.hora_entrada:
            return "sin_entrada"

        if self.hora_entrada and not self.hora_salida:
            return "salida_pendiente"

        return "asistencia_completa"

    @property
    def estado_badge(self):
        if self.estado == "salida_automatica":
            return "info"

        if not self.hora_entrada:
            return "secondary"

        if self.hora_entrada and not self.hora_salida:
            if self.es_extraordinario:
                return "primary"
            return "warning"

        if self.es_extraordinario:
            return "primary"

        if self.tiene_retardo:
            return "danger"

        return "success"

    @property
    def observacion_calculada(self):
        if not self.hora_entrada:
            return "No se registró entrada."

        if self.hora_entrada and not self.hora_salida:
            if self.es_extraordinario:
                return "El usuario registró entrada fuera del horario laboral configurado, pero aún no registra salida."
            return "El usuario registró entrada, pero aún no registra salida."

        if self.estado == "salida_automatica":
            return "El usuario no registró salida. El sistema cerró la asistencia automáticamente."

        if self.es_extraordinario:
            return "Asistencia registrada fuera del horario laboral configurado."

        if self.tiene_retardo:
            return "Asistencia completa con retardo."

        return "Asistencia completa."

    def __str__(self):
        return (
            f"Asistencia: "
            f"{self.usuario.username if self.usuario else 'Usuario eliminado'} "
            f"- {self.fecha}"
        )

    class Meta:
        ordering = ["-fecha"]


# =========================
# Tareas
# =========================
class Tarea(models.Model):

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="tareas",
        verbose_name="Usuario"
    )

    descripcion = models.TextField(verbose_name="Descripción")
    fecha_asignada = models.DateField(auto_now_add=True)
    fecha_limite = models.DateField(verbose_name="Fecha límite")

    def __str__(self):
        return f"Tarea: {self.descripcion} - {self.usuario.username}"

    class Meta:
        ordering = ["-fecha_asignada"]


# =========================
# Reportes
# =========================
class Reporte(models.Model):

    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ["-fecha_creacion"]


# =========================
# Notificaciones
# =========================
class Notification(models.Model):

    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación: {self.message} - {self.created_at}"

    class Meta:
        ordering = ["-created_at"]


# =========================
# Resumen asistencia
# =========================
class AttendanceSummary(models.Model):

    present = models.IntegerField()
    absent = models.IntegerField()
    late = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Resumen: {self.date}"

    class Meta:
        ordering = ["-date"]

# =========================
# Configuración de Asistencia
# =========================
class ConfiguracionAsistencia(models.Model):

    nombre = models.CharField(
        max_length=100,
        default="Configuración general",
        verbose_name="Nombre"
    )

    hora_entrada = models.TimeField(
        default=time(9, 0),
        verbose_name="Hora de entrada"
    )

    tolerancia_minutos = models.PositiveIntegerField(
        default=15,
        verbose_name="Tolerancia en minutos"
    )

    hora_salida_automatica = models.TimeField(
        default=time(23, 59),
        verbose_name="Hora de salida automática"
    )

    hora_limite_extraordinario = models.TimeField(
    default=time(18, 0),
    verbose_name="Hora límite para asistencia fuera de horario"
    )

    activa = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )

    def hora_limite_retardo(self):
        from datetime import datetime, timedelta

        base = datetime.combine(datetime.today(), self.hora_entrada)
        limite = base + timedelta(minutes=self.tolerancia_minutos)
        return limite.time()

    def __str__(self):
        return f"{self.nombre} - Entrada {self.hora_entrada}"

    class Meta:
        verbose_name = "Configuración de asistencia"
        verbose_name_plural = "Configuraciones de asistencia"


# =========================
# Personal (NORMALIZADO)
# =========================
class Personal(models.Model):

    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre completo"
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico"
    )

    telefono = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )

    departamento = models.CharField(
        max_length=50,
        choices=[
            ("Recursos Humanos", "Recursos Humanos"),
            ("IT", "IT"),
            ("Finanzas", "Finanzas"),
            ("Operaciones", "Operaciones"),
        ],
        verbose_name="Departamento",
    )

    comentarios = models.TextField(
        blank=True,
        null=True,
        verbose_name="Comentarios adicionales"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.nombre = nombre_bonito(self.nombre)
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre"]


# =========================
# Eventos
# =========================
class Evento(models.Model):

    titulo = models.CharField(max_length=100)
    fecha = models.DateField()
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ["-fecha"]


# =========================
# Mensajes (Comunicación interna)
# =========================
class Mensaje(models.Model):
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensajes_enviados",
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensajes_recibidos",
    )

    asunto = models.CharField(max_length=160)
    cuerpo = models.TextField()

    archivo = models.FileField(
        upload_to="mensajes_adjuntos/%Y/%m/",
        blank=True,
        null=True
    )

    leido = models.BooleanField(default=False, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)
    en_papelera = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        rem = self.remitente.username if self.remitente else "Usuario eliminado"
        des = self.destinatario.username if self.destinatario else "Usuario eliminado"
        return f"{self.asunto} ({rem} -> {des})"


class BitacoraAcceso(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bitacora_accesos"
    )

    fecha = models.DateField(auto_now_add=True)
    hora_entrada = models.DateTimeField(null=True, blank=True)
    hora_salida = models.DateTimeField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    @property
    def duracion_sesion(self):
        if not self.hora_entrada:
            return None

        if self.hora_salida:
            return self.hora_salida - self.hora_entrada

        return timezone.now() - self.hora_entrada
    
    @property
    def duracion_segundos(self):
        duracion = self.duracion_sesion

        if not duracion:
            return 0
        
        return int(duracion.total_seconds())

    def __str__(self):
        return f"{self.usuario} - {self.fecha}"
    
# =========================
# Capacitaciones
# =========================
class Capacitacion(models.Model):

    MODALIDAD_CHOICES = [
        ("Presencial", "Presencial"),
        ("En línea", "En línea"),
        ("Mixta", "Mixta"),
    ]

    ESTADO_CHOICES = [
        ("activa", "Activa"),
        ("inactiva", "Inactiva"),
    ]

    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre de la capacitación"
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )

    duracion_horas = models.PositiveIntegerField(
        default=1,
        verbose_name="Duración en horas"
    )

    modalidad = models.CharField(
        max_length=20,
        choices=MODALIDAD_CHOICES,
        default="Presencial",
        verbose_name="Modalidad"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="activa",
        db_index=True,
        verbose_name="Estado"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capacitaciones_creadas",
        verbose_name="Creado por"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Capacitación"
        verbose_name_plural = "Capacitaciones"

class MaterialCapacitacion(models.Model):
    capacitacion = models.ForeignKey(
        Capacitacion,
        on_delete=models.CASCADE,
        related_name="materiales",
        verbose_name="Capacitación"
    )

    titulo = models.CharField(
        max_length=150,
        verbose_name="Título del material"
    )

    archivo = models.FileField(
        upload_to="capacitaciones_materiales/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Archivo"
    )

    enlace = models.URLField(
        blank=True,
        null=True,
        verbose_name="Enlace externo"
    )

    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de subida"
    )

    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materiales_capacitacion_subidos",
        verbose_name="Subido por"
    )

    def __str__(self):
        return f"{self.capacitacion.nombre} - {self.titulo}"

    class Meta:
        ordering = ["-fecha_subida"]
        verbose_name = "Material de capacitación"
        verbose_name_plural = "Materiales de capacitación"


class CapacitacionAsignada(models.Model):

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_proceso", "En proceso"),
        ("aprobada", "Aprobada"),
        ("vencida", "Vencida"),
        ("cancelada", "Cancelada"),
    ]

    capacitacion = models.ForeignKey(
        Capacitacion,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        verbose_name="Capacitación"
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="capacitaciones_asignadas",
        verbose_name="Usuario asignado"
    )

    fecha_asignacion = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de asignación"
    )

    fecha_limite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha límite"
    )

    fecha_realizacion = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de realización"
    )

    fecha_vencimiento = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de vencimiento"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="pendiente",
        db_index=True,
        verbose_name="Estado"
    )

    constancia = models.FileField(
        upload_to="capacitaciones_constancias/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Constancia"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    @property
    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None

        return (self.fecha_vencimiento - timezone.localdate()).days

    @property
    def esta_vencida(self):
        dias = self.dias_para_vencer

        if dias is None:
            return False

        return dias < 0

    @property
    def proxima_a_vencer(self):
        dias = self.dias_para_vencer

        if dias is None:
            return False

        return 0 <= dias <= 30

    @property
    def estado_visual(self):
        if self.estado == "pendiente":
            return "Pendiente"

        if self.estado == "en_proceso":
            return "En proceso"

        if self.estado == "aprobada":
            return "Aprobada"

        if self.estado == "vencida":
            return "Vencida"

        if self.estado == "cancelada":
            return "Cancelada"

        return "Pendiente"

    @property
    def estado_badge(self):
        if self.estado == "pendiente":
            return "warning"

        if self.estado == "en_proceso":
            return "info"

        if self.estado == "aprobada":
            return "success"

        if self.estado == "vencida":
            return "danger"

        if self.estado == "cancelada":
            return "secondary"

        return "warning"

    def __str__(self):
        return f"{self.usuario.username} - {self.capacitacion.nombre}"

    class Meta:
        ordering = ["-fecha_asignacion"]
        verbose_name = "Capacitación asignada"
        verbose_name_plural = "Capacitaciones asignadas"
        constraints = [
            models.UniqueConstraint(
                fields=["capacitacion", "usuario"],
                name="uniq_capacitacion_usuario"
            )
        ]