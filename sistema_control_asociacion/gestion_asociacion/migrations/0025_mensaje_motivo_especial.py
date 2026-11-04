from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gestion_asociacion", "0024_usuario_email_verificado"),
    ]

    operations = [
        migrations.AddField(
            model_name="mensaje",
            name="motivo_especial",
            field=models.CharField(
                blank=True,
                choices=[
                    ("problema_no_resuelto", "Problema no resuelto por administración"),
                    ("queja_administrativa", "Queja relacionada con un administrador"),
                    ("asunto_confidencial", "Asunto confidencial"),
                    ("otro", "Otro caso especial"),
                ],
                default="",
                max_length=40,
                verbose_name="Motivo de comunicación especial",
            ),
        ),
    ]
