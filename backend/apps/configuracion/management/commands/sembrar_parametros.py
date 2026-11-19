import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.configuracion.models import ParametroSistema

FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'parametros_iniciales.json'


class Command(BaseCommand):
    help = (
        'Crea los parámetros del sistema que falten (parametros_iniciales.json). '
        'Es idempotente y nunca modifica un parámetro que ya existe.'
    )

    def handle(self, *args, **options):
        existentes = set(ParametroSistema.objects.values_list('clave', flat=True))
        nuevos = []
        for entrada in json.loads(FIXTURE.read_text(encoding='utf-8')):
            campos = entrada['fields']
            if campos['clave'] in existentes:
                continue
            nuevos.append(ParametroSistema(
                clave=campos['clave'],
                valor=campos['valor'],
                descripcion=campos.get('descripcion', ''),
                categoria=campos['categoria'],
                tipo_dato=campos['tipo_dato'],
            ))
        # bulk_create: ParametroSistema.save() valida y rechaza valores vacíos (p. ej. logo_url)
        ParametroSistema.objects.bulk_create(nuevos)
        self.stdout.write(f'Parámetros creados: {len(nuevos)}')
