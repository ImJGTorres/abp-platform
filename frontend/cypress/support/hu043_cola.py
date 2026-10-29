"""
Apoyo de la prueba de aceptación de HU-043 (frontend/cypress/e2e/hu043-correos.cy.js).
Cypress no puede leer una bandeja de correo, así que este script consulta cola_correo y
renderiza el HTML que se enviaría (renderizar_correo). NO envía ningún correo.

Uso (desde backend/): python ../frontend/cypress/support/hu043_cola.py <datos|cola> [asunto]
Imprime una línea JSON.
"""
import json
import os
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.utils import timezone  # noqa: E402

from apps.alertas.management.commands.run_scheduler import TAREAS  # noqa: E402
from apps.alertas.models import Alerta, ColaCorreo  # noqa: E402
from apps.alertas.services import renderizar_correo  # noqa: E402
from apps.entregables.models import Notificacion  # noqa: E402
from apps.evaluacion.models import Evaluacion  # noqa: E402
from apps.cursos.models import Proyecto  # noqa: E402

PREFIJO = '[DEMO HU-043]'
accion = sys.argv[1]

if accion == 'datos':
    proyecto = Proyecto.objects.get(nombre=f'{PREFIJO} Proyecto')
    evaluacion = Evaluacion.objects.get(id_entregable__titulo=f'{PREFIJO} Informe final')
    print(json.dumps({'proyecto_id': proyecto.id, 'evaluacion_id': evaluacion.id}))

elif accion == 'cola':
    asunto = sys.argv[2]
    correos = list(ColaCorreo.objects.filter(asunto=asunto).select_related('id_usuario_destino')
                   .order_by('id'))
    ahora = timezone.now()
    intervalo = next(m for nombre, _, m in TAREAS if nombre == 'correos')
    salida = {
        'intervalo_scheduler_min': intervalo,
        'correos': [{
            'destino': c.id_usuario_destino.correo,
            'plantilla': c.plantilla,
            'estado': c.estado,
            'segundos_desde_encolado': round((ahora - c.fecha_creacion).total_seconds(), 1),
            'html': renderizar_correo(c),
        } for c in correos],
        # Lo que vería la campanita de cada destinatario (alertas y notificaciones)
        'campanita': {c.id_usuario_destino.correo: (
            Alerta.objects.filter(id_usuario_destino=c.id_usuario_destino).count()
            + Notificacion.objects.filter(id_usuario_destino=c.id_usuario_destino).count()
        ) for c in correos},
    }
    print(json.dumps(salida))
