from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from .models import CriterioRubrica, NivelDesempeno, Rubrica


def validar_ponderaciones(rubrica):
    """HU-044 (SCRUM-564): la suma de peso_porcentual de los criterios debe ser exactamente 100."""
    suma = rubrica.criterios.aggregate(total=Sum('peso_porcentual'))['total'] or Decimal('0')
    if suma != Decimal('100'):
        raise ValidationError({
            'detail': f'La suma de las ponderaciones de los criterios debe ser 100 %. Suma actual: {suma} %.',
            'suma_actual': suma,
        })


def clonar_rubrica(plantilla, id_proyecto, docente):
    """
    HU-044 (SCRUM-563): copia la plantilla con sus criterios y niveles como rúbrica
    independiente del proyecto. La copia no comparte filas con la plantilla.
    """
    validar_ponderaciones(plantilla)
    with transaction.atomic():
        copia = Rubrica.objects.create(
            id_proyecto_id=id_proyecto,
            id_docente=docente,
            nombre=plantilla.nombre,
            descripcion=plantilla.descripcion,
            tipo=plantilla.tipo,
            peso_total=plantilla.peso_total,
            es_plantilla=False,
            nombre_plantilla=None,
        )
        for criterio in plantilla.criterios.prefetch_related('niveles'):
            nuevo = CriterioRubrica.objects.create(
                id_rubrica=copia,
                nombre=criterio.nombre,
                descripcion=criterio.descripcion,
                peso_porcentual=criterio.peso_porcentual,
                id_rap_id=criterio.id_rap_id,
            )
            NivelDesempeno.objects.bulk_create([
                NivelDesempeno(
                    id_criterio=nuevo,
                    nivel=n.nivel,
                    etiqueta=n.etiqueta,
                    descripcion=n.descripcion,
                    puntos=n.puntos,
                )
                for n in criterio.niveles.all()
            ])
    return copia
