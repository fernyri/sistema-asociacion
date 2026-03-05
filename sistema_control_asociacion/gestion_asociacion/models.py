from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.functions import Lower


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
    partes = str(valor).strip().split()  # ✅ split() ya colapsa espacios
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

        # ✅ Email siempre normalizado
        email = (self.normalize_email(email) or "").strip().lower()

        # ✅ Username limpio (colapsa espacios)
        username_clean = " ".join((username or "").strip().split())

        user = self.model(
            username=username_clean,
            email=email,
            **extra_fields
        )

        user.set_password(password)

        # ✅ username_norm obligatorio antes de validar (case-insensitive real + espacios)
        user.username_norm = username_norm_value(username_clean)

        # ✅ Validaciones del modelo
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # ✅ Tu app decide el acceso por rol, así que el superuser debe ser Administrador
        extra_fields.setdefault("rol", "Administrador")

        return self.create_user(username, email, password, **extra_fields)


# =========================
# Usuario personalizado
# =========================
class Usuario(AbstractUser):

    # ✅ Email único (y lo guardamos siempre en minúsculas en save())
    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico"
    )

    # ✅ Username case-insensitive real (y además soporta espacios colapsados)
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

        # ✅ Email siempre minúscula
        self.email = (self.email or "").strip().lower()

        # ✅ Guardado bonito (también colapsa espacios)
        self.username = nombre_bonito(self.username)
        self.first_name = nombre_bonito(self.first_name)
        self.last_name = nombre_bonito(self.last_name)

        # ✅ Username normalizado (Luis == luis) + espacios colapsados
        self.username_norm = username_norm_value(self.username)

        super().save(*args, **kwargs)

    # =========================
    # Helpers de rol
    # =========================
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

        # ✅ Unicidad real de email sin importar mayúsculas (recomendado)
        constraints = [
            models.UniqueConstraint(Lower("email"), name="uniq_usuario_email_lower"),
        ]


# =========================
# Asistencia
# =========================
class Asistencia(models.Model):

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

    # =========================
    # SAVE NORMALIZADO
    # =========================
    def save(self, *args, **kwargs):

        # ✅ Nombre bonito
        self.nombre = nombre_bonito(self.nombre)

        # ✅ Email minúscula
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

    # ✅ Papelera (soft-delete)
    en_papelera = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        rem = self.remitente.username if self.remitente else "Usuario eliminado"
        des = self.destinatario.username if self.destinatario else "Usuario eliminado"
        return f"{self.asunto} ({rem} -> {des})"
