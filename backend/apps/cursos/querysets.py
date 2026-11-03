from django.db import models
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce


class FaseProyectoQuerySet(models.QuerySet):
    """QuerySet de FaseProyecto con anotaciones de resumen de actividades."""

    def con_resumen_actividades(self):
        """Anota cada fase con conteos de actividades por estado (1 query extra vía JOIN)."""
        return self.annotate(
            total_actividades=Count('actividades', distinct=True),
            actividades_completadas=Count(
                'actividades',
                filter=Q(actividades__estado='completada'),
                distinct=True,
            ),
            actividades_en_progreso=Count(
                'actividades',
                filter=Q(actividades__estado='en_progreso'),
                distinct=True,
            ),
            actividades_bloqueadas=Count(
                'actividades',
                filter=Q(actividades__estado='bloqueada'),
                distinct=True,
            ),
        )


class ProyectoQuerySet(models.QuerySet):
    """QuerySet de Proyecto con anotaciones de progreso agregado por fases."""

    def con_progreso(self):
        """
        Anota cada proyecto con métricas de progreso calculadas en una sola
        query SQL (GROUP BY), evitando N+1 al listar proyectos.

        Campos añadidos:
          porcentaje_progreso      — avance real de vista_progreso_proyecto (promedio por actividad)
          total_fases              — número de fases del proyecto
          fases_completadas        — fases en estado 'completada'
          fases_en_progreso        — fases en estado 'en_progreso'
          total_actividades        — actividades en todas las fases
          actividades_completadas  — actividades en estado 'completada'
        """
        from .models import VistaProgresoProyecto  # evita import circular (models importa este módulo)

        return self.annotate(
            total_fases=Count('fases', distinct=True),
            fases_completadas=Count(
                'fases',
                filter=Q(fases__estado='completada'),
                distinct=True,
            ),
            fases_en_progreso=Count(
                'fases',
                filter=Q(fases__estado='en_progreso'),
                distinct=True,
            ),
            porcentaje_progreso=Coalesce(
                Subquery(VistaProgresoProyecto.objects.filter(id_proyecto=OuterRef('pk'))
                         .values('porcentaje_progreso')[:1]),
                Value(0),
                output_field=IntegerField(),
            ),
            total_actividades=Count('fases__actividades', distinct=True),
            actividades_completadas=Count(
                'fases__actividades',
                filter=Q(fases__actividades__estado='completada'),
                distinct=True,
            ),
        )
