import pytest
from django.core.management import call_command

from apps.configuracion.models import ParametroSistema


@pytest.mark.django_db
def test_sembrar_parametros_crea_los_faltantes_y_no_pisa_los_existentes():
    ParametroSistema.objects.filter(clave='max_estudiantes_por_equipo').delete()
    ParametroSistema.objects.update_or_create(
        clave='semanas_sprint',
        defaults={'valor': '4', 'categoria': 'general', 'tipo_dato': 'integer'},
    )

    call_command('sembrar_parametros')

    assert ParametroSistema.objects.get(clave='max_estudiantes_por_equipo').valor == '5'
    assert ParametroSistema.objects.get(clave='semanas_sprint').valor == '4'  # no se pisó

    total = ParametroSistema.objects.count()
    call_command('sembrar_parametros')  # idempotente
    assert ParametroSistema.objects.count() == total
