from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bitacora', '0002_alter_bitacorasistema_accion'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE bitacora_sistema
                    DROP CONSTRAINT IF EXISTS bitacora_sistema_id_usuario_042e7f68_fk_usuario_id;

                ALTER TABLE bitacora_sistema
                    ADD CONSTRAINT bitacora_sistema_id_usuario_042e7f68_fk_usuario_id
                    FOREIGN KEY (id_usuario)
                    REFERENCES usuario(id)
                    ON DELETE SET NULL
                    DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                ALTER TABLE bitacora_sistema
                    DROP CONSTRAINT IF EXISTS bitacora_sistema_id_usuario_042e7f68_fk_usuario_id;

                ALTER TABLE bitacora_sistema
                    ADD CONSTRAINT bitacora_sistema_id_usuario_042e7f68_fk_usuario_id
                    FOREIGN KEY (id_usuario)
                    REFERENCES usuario(id)
                    DEFERRABLE INITIALLY DEFERRED;
            """,
        ),
    ]
