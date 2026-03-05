from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from .models import Usuario, Mensaje


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
    partes = str(valor).strip().split()  # split() ya colapsa espacios

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
    ✅ Normalización real para unicidad:
    - strip
    - colapsa espacios
    - lower
    """
    v = " ".join(str(v or "").strip().split())
    return v.lower()


class RegistroForm(UserCreationForm):
    telefono = forms.CharField(
        label="Número de teléfono",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Introduce tu número de teléfono (opcional)",
            "maxlength": "12"
        })
    )

    direccion = forms.CharField(
        label="Dirección",
        required=False,
        widget=forms.Textarea(attrs={
            "placeholder": "Introduce tu dirección",
            "rows": 2
        })
    )

    genero = forms.ChoiceField(
        label="Género",
        choices=[("M", "Masculino"), ("F", "Femenino"), ("O", "Otro")],
        widget=forms.Select()
    )

    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        widget=forms.DateInput(attrs={
            "type": "date",
            "placeholder": "Selecciona tu fecha de nacimiento"
        })
    )

    class Meta:
        model = Usuario
        fields = [
            "username", "first_name", "last_name", "email",
            "telefono", "direccion", "genero", "fecha_nacimiento",
            "password1", "password2",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Introduce un nombre de usuario"}),
            "first_name": forms.TextInput(attrs={"placeholder": "Ingresa tu nombre"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Ingresa tu apellido"}),
            "email": forms.EmailInput(attrs={"placeholder": "Introduce tu correo electrónico"}),
        }

    # -------------------------
    # Helpers de normalización
    # -------------------------
    def _display_texto(self, v: str) -> str:
        return nombre_bonito(v)

    def _norm_email(self, v: str) -> str:
        v = (v or "").strip()
        v = BaseUserManager.normalize_email(v)
        return (v or "").lower()

    # -------------------------
    # Clean fields
    # -------------------------
    def clean_username(self):
        raw = self.cleaned_data.get("username")
        uname_display = self._display_texto(raw)          # lo que se guarda/ve
        uname_norm = username_norm_value(uname_display)  # lo que se compara (igual que models.py)

        # ✅ Comparación contra username_norm (case-insensitive real)
        if Usuario.objects.filter(username_norm=uname_norm).exists():
            raise forms.ValidationError("El nombre de usuario ya está registrado. Prueba con otro.")

        return uname_display

    def clean_first_name(self):
        return self._display_texto(self.cleaned_data.get("first_name"))

    def clean_last_name(self):
        return self._display_texto(self.cleaned_data.get("last_name"))

    def clean_email(self):
        email = self._norm_email(self.cleaned_data.get("email"))
        # ✅ El modelo ya tiene constraint uniq lower, pero dejamos mensaje amigable
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("El correo electrónico ya está en uso. Usa otro.")
        return email

    def clean_telefono(self):
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if telefono:
            # ✅ solo dígitos, longitud “sana”
            if not telefono.isdigit():
                raise forms.ValidationError("El número de teléfono debe contener solo dígitos.")
            if len(telefono) < 7:
                raise forms.ValidationError("El teléfono debe tener al menos 7 dígitos.")
            if len(telefono) > 15:
                raise forms.ValidationError("El teléfono es demasiado largo.")
        return telefono

    def clean_direccion(self):
        direccion = (self.cleaned_data.get("direccion") or "").strip()
        # ✅ Si la capturan, que no sea “xx”
        if direccion and len(direccion) < 10:
            raise forms.ValidationError("La dirección debe tener al menos 10 caracteres.")
        return direccion

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get("fecha_nacimiento")
        if fecha_nacimiento:
            hoy = timezone.localdate()
            if fecha_nacimiento > hoy:
                raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return fecha_nacimiento

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        # ✅ username ya viene “bonito”; normalizamos igual que el modelo
        username = self.cleaned_data.get("username") or ""
        uname_norm = username_norm_value(username)

        if password:
            self.validar_password_segura(password, uname_norm)

        return password

    def validar_password_segura(self, password: str, username_norm: str):
        username_norm = (username_norm or "")
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if username_norm and username_norm in password.lower():
            raise ValidationError("La contraseña no puede contener el nombre de usuario.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("La contraseña debe incluir al menos un número.")
        if not any(char.isalpha() for char in password):
            raise ValidationError("La contraseña debe incluir al menos una letra.")

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned_data

    # -------------------------
    # Save
    # -------------------------
    def save(self, commit=True):
        user = super().save(commit=False)

        # ✅ Guardado “bonito”
        user.username = self._display_texto(user.username)
        user.first_name = self._display_texto(user.first_name)
        user.last_name = self._display_texto(user.last_name)

        # ✅ Email siempre minúsculas
        user.email = self._norm_email(user.email)

        # ✅ SIEMPRE registrar como Miembro
        user.rol = "Miembro"

        if commit:
            user.save()
        return user

class MensajeForm(forms.ModelForm):
    class Meta:
        model = Mensaje
        fields = ["asunto", "cuerpo", "archivo"]
        widgets = {
            "asunto": forms.TextInput(attrs={"placeholder": "Asunto", "class": "form-control"}),
            "cuerpo": forms.Textarea(attrs={"placeholder": "Escribe tu mensaje...", "class": "form-control", "rows": 5}),
        }

    def clean_asunto(self):
        asunto = (self.cleaned_data.get("asunto") or "").strip()
        if not asunto:
            raise forms.ValidationError("El asunto es obligatorio.")
        return asunto

    def clean_cuerpo(self):
        cuerpo = (self.cleaned_data.get("cuerpo") or "").strip()
        if not cuerpo:
            raise forms.ValidationError("El mensaje no puede ir vacío.")
        return cuerpo
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if archivo and archivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("El archivo no debe superar 5MB.")
        return archivo
