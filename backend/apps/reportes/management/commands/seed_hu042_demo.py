"""
Datos de demostración para la prueba de aceptación de HU-042 (SCRUM-557):
panel de semáforos de proyectos del docente.

No crea proyectos nuevos: el docente demo de HU-040 (demo.docente.hu040@ufps.edu.co)
ya tiene 3 proyectos reales con niveles distintos (2 rojo, 1 verde), suficiente para
probar el panel, el filtro por color y la navegación al detalle. Solo le asigna una
contraseña conocida para poder iniciar sesión en Cypress.
"""
from django.core.management.base import BaseCommand

CORREO_DOCENTE = 'demo.docente.hu040@ufps.edu.co'
PASSWORD = 'Test1234'


class Command(BaseCommand):
    help = 'Asigna una contraseña conocida al docente demo para la prueba de aceptación de HU-042.'

    def handle(self, *args, **options):
        from apps.reportes.semaforo import semaforos_docente
        from apps.usuarios.models import Usuario

        docente, creado = Usuario.objects.get_or_create(
            correo=CORREO_DOCENTE,
            defaults={'nombre': 'Docente', 'apellido': 'Demo HU-040',
                      'tipo_rol': Usuario.TipoRol.DOCENTE},
        )
        docente.set_password(PASSWORD)
        docente.save(update_fields=['password'])

        niveles = [p['nivel'] for p in semaforos_docente(docente.id)]
        self.stdout.write(self.style.SUCCESS(
            f"Listo. Docente: {CORREO_DOCENTE} / {PASSWORD} "
            f"({'creado' if creado else 'ya existía'}). Niveles actuales: {niveles}."
        ))
