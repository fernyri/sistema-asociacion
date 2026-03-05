from django.db import migrations, models

def backfill_username_norm(apps, schema_editor):
    Usuario = apps.get_model("gestion_asociacion", "Usuario")
    for u in Usuario.objects.all().only("id", "username", "email", "username_norm"):
        username = " ".join((u.username or "").strip().split())
        username_norm = (username or "").lower()
        email = (u.email or "").strip().lower()

        # solo actualiza si hace falta
        updates = {}
        if u.username != username:
            updates["username"] = username
        if u.username_norm != username_norm:
            updates["username_norm"] = username_norm
        if u.email != email:
            updates["email"] = email

        if updates:
            Usuario.objects.filter(id=u.id).update(**updates)

class Migration(migrations.Migration):

    dependencies = [
        ("gestion_asociacion", "0005_usuario_username_norm"),
    ]

    operations = [
        migrations.RunPython(backfill_username_norm, migrations.RunPython.noop),

        # ✅ ahora sí: forzamos NOT NULL
        migrations.AlterField(
            model_name="usuario",
            name="username_norm",
            field=models.CharField(
                max_length=150,
                unique=True,
                editable=False,
                db_index=True,
                verbose_name="Username normalizado",
            ),
        ),
    ]
