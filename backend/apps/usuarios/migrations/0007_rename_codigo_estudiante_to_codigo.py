from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_add_codigo_estudiante'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usuario',
            old_name='codigo_estudiante',
            new_name='codigo',
        ),
    ]
