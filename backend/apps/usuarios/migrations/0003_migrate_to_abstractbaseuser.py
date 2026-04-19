from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_usuariorol'),
    ]

    operations = [
        # RenameField: renombra la columna 'contrasena_hash' a 'password' en la tabla 'usuario'.
        # AbstractBaseUser espera encontrar una columna llamada 'password' para leer y escribir
        # los hashes de contraseña. Los datos existentes en 'contrasena_hash' se conservan
        # intactos — solo cambia el nombre de la columna en la base de datos.
        migrations.RenameField(
            model_name='usuario',
            old_name='contrasena_hash',
            new_name='password',
        ),
        # AddField: agrega la columna 'last_login' que AbstractBaseUser incluye por defecto.
        # Django la usa para registrar cuándo el usuario se autenticó por última vez.
        # Es nullable (blank=True, null=True) porque los usuarios existentes aún no tienen
        # ningún login registrado con el nuevo sistema.
        migrations.AddField(
            model_name='usuario',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last login'),
        ),
    ]