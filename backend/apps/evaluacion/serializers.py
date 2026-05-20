from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.cursos.models import Actividad, Proyecto, ResultadoAprendizaje
from apps.equipos.models import Equipo
from apps.usuarios.models import Usuario
from .models import (
    Autoevaluacion,
    CalificacionCriterio,
    Coevaluacion,
    CriterioRubrica,
    DetalleCoevaluacion,
    DetalleAutoevaluacion,
    Evaluacion,
    NivelDesempeno,
    Retroalimentacion,
    Rubrica,
)


# ---------------------------------------------------------------------------
# NivelDesempeno
# ---------------------------------------------------------------------------

class NivelDesempenoSerializer(serializers.ModelSerializer):
    etiqueta_display = serializers.CharField(source='get_etiqueta_display', read_only=True)

    class Meta:
        model = NivelDesempeno
        fields = ['id', 'nivel', 'etiqueta', 'etiqueta_display', 'descripcion', 'puntos']
        read_only_fields = fields


class NivelDesempenoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = NivelDesempeno
        fields = ['nivel', 'etiqueta', 'descripcion', 'puntos']

    def validate_nivel(self, value):
        if not (1 <= value <= 4):
            raise serializers.ValidationError('El nivel debe estar entre 1 y 4.')
        return value

    def validate_puntos(self, value):
        if value < 0:
            raise serializers.ValidationError('Los puntos no pueden ser negativos.')
        return value


# ---------------------------------------------------------------------------
# CriterioRubrica
# ---------------------------------------------------------------------------

class CriterioRubricaSerializer(serializers.ModelSerializer):
    niveles = NivelDesempenoSerializer(many=True, read_only=True)
    rap_detalle = serializers.SerializerMethodField()

    class Meta:
        model = CriterioRubrica
        fields = ['id', 'nombre', 'descripcion', 'peso_porcentual', 'id_rap', 'rap_detalle', 'niveles']
        read_only_fields = fields

    def get_rap_detalle(self, obj):
        rap = obj.id_rap
        if rap is None:
            return None
        return {'id': rap.pk, 'nombre': rap.nombre, 'descripcion': rap.descripcion}


class CriterioRubricaWriteSerializer(serializers.ModelSerializer):
    niveles = NivelDesempenoWriteSerializer(many=True)
    id_rap = serializers.PrimaryKeyRelatedField(
        queryset=ResultadoAprendizaje.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = CriterioRubrica
        fields = ['nombre', 'descripcion', 'peso_porcentual', 'id_rap', 'niveles']

    def validate_peso_porcentual(self, value):
        if value <= 0:
            raise serializers.ValidationError('El peso porcentual debe ser mayor a 0.')
        if value > 100:
            raise serializers.ValidationError('El peso porcentual no puede superar 100.')
        return value

    def validate_niveles(self, value):
        if not value:
            raise serializers.ValidationError(
                'Cada criterio debe tener al menos un nivel de desempeño.'
            )
        niveles = [n['nivel'] for n in value]
        if len(niveles) != len(set(niveles)):
            raise serializers.ValidationError(
                'No puede haber niveles duplicados dentro de un criterio.'
            )
        return value


# ---------------------------------------------------------------------------
# Rubrica
# ---------------------------------------------------------------------------

class RubricaSerializer(serializers.ModelSerializer):
    criterios = CriterioRubricaSerializer(many=True, read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    docente_nombre = serializers.SerializerMethodField()
    proyecto_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Rubrica
        fields = [
            'id',
            'nombre',
            'descripcion',
            'tipo',
            'tipo_display',
            'peso_total',
            'id_proyecto',
            'proyecto_nombre',
            'id_docente',
            'docente_nombre',
            'fecha_creacion',
            'criterios',
        ]
        read_only_fields = fields

    def get_docente_nombre(self, obj):
        d = obj.id_docente
        if d is None:
            return None
        return f'{d.nombre} {d.apellido}'

    def get_proyecto_nombre(self, obj):
        return obj.id_proyecto.nombre if obj.id_proyecto else None


class RubricaCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/rubricas/ — crea una rúbrica completa en una sola llamada,
    incluyendo sus criterios de evaluación y los niveles de desempeño de cada criterio.

    Validaciones:
    - La rúbrica debe tener al menos un criterio.
    - La suma de peso_porcentual de todos los criterios debe ser exactamente 100.
    - Cada criterio debe tener al menos un nivel (entre 1 y 4).
    - No puede haber niveles duplicados dentro de un mismo criterio.
    """
    criterios = CriterioRubricaWriteSerializer(many=True)
    id_proyecto = serializers.PrimaryKeyRelatedField(
        queryset=Proyecto.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Rubrica
        fields = ['nombre', 'descripcion', 'tipo', 'peso_total', 'id_proyecto', 'criterios']

    def validate_criterios(self, value):
        if not value:
            raise serializers.ValidationError('La rúbrica debe tener al menos un criterio.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        criterios = attrs.get('criterios', [])
        if criterios:
            total = sum(c['peso_porcentual'] for c in criterios)
            if abs(float(total) - 100.0) > 0.01:
                raise serializers.ValidationError({
                    'criterios': (
                        f'La suma de los pesos porcentuales de los criterios debe ser 100. '
                        f'Suma actual: {total}.'
                    )
                })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        criterios_data = validated_data.pop('criterios')
        rubrica = Rubrica.objects.create(**validated_data)
        for criterio_data in criterios_data:
            niveles_data = criterio_data.pop('niveles')
            criterio = CriterioRubrica.objects.create(id_rubrica=rubrica, **criterio_data)
            NivelDesempeno.objects.bulk_create([
                NivelDesempeno(id_criterio=criterio, **nivel_data)
                for nivel_data in niveles_data
            ])
        return rubrica

    def to_representation(self, instance):
        return RubricaSerializer(instance, context=self.context).data


class RubricaUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/rubricas/<pk>/ — actualiza solo los campos escalares de la rúbrica."""
    id_proyecto = serializers.PrimaryKeyRelatedField(
        queryset=Proyecto.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Rubrica
        fields = ['nombre', 'descripcion', 'tipo', 'peso_total', 'id_proyecto']

    def to_representation(self, instance):
        return RubricaSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# HU-23: BE-02/BE-03 — Rúbricas por proyecto
# ---------------------------------------------------------------------------

class RubricaProyectoCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/proyectos/<proyecto_id>/rubricas/
    id_proyecto e id_docente se inyectan desde la vista.
    peso_total se calcula como suma de los puntos máximos de cada criterio.
    """
    criterios = CriterioRubricaWriteSerializer(many=True)

    class Meta:
        model = Rubrica
        fields = ['nombre', 'descripcion', 'tipo', 'criterios']

    def validate_criterios(self, value):
        if not value:
            raise serializers.ValidationError('La rúbrica debe tener al menos un criterio.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        criterios = attrs.get('criterios', [])
        if criterios:
            total = sum(c['peso_porcentual'] for c in criterios)
            if abs(float(total) - 100.0) > 0.01:
                raise serializers.ValidationError({
                    'criterios': (
                        f'La suma de los pesos porcentuales debe ser exactamente 100. '
                        f'Suma actual: {total}.'
                    )
                })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        criterios_data = validated_data.pop('criterios')
        peso_total = sum(
            max(n['puntos'] for n in c['niveles'])
            for c in criterios_data
        )
        rubrica = Rubrica.objects.create(peso_total=peso_total, **validated_data)
        for criterio_data in criterios_data:
            niveles_data = criterio_data.pop('niveles')
            criterio = CriterioRubrica.objects.create(id_rubrica=rubrica, **criterio_data)
            NivelDesempeno.objects.bulk_create([
                NivelDesempeno(id_criterio=criterio, **nivel_data)
                for nivel_data in niveles_data
            ])
        return rubrica

    def to_representation(self, instance):
        return RubricaSerializer(instance, context=self.context).data


class RubricaFullUpdateSerializer(serializers.ModelSerializer):
    """
    PUT /api/rubricas/<pk>/ — reemplaza criterios y niveles en su totalidad.
    peso_total se recalcula como suma de puntos máximos de cada criterio.
    """
    criterios = CriterioRubricaWriteSerializer(many=True)

    class Meta:
        model = Rubrica
        fields = ['nombre', 'descripcion', 'tipo', 'criterios']

    def validate_criterios(self, value):
        if not value:
            raise serializers.ValidationError('La rúbrica debe tener al menos un criterio.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        criterios = attrs.get('criterios', [])
        if criterios:
            total = sum(c['peso_porcentual'] for c in criterios)
            if abs(float(total) - 100.0) > 0.01:
                raise serializers.ValidationError({
                    'criterios': (
                        f'La suma de los pesos porcentuales debe ser exactamente 100. '
                        f'Suma actual: {total}.'
                    )
                })
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        criterios_data = validated_data.pop('criterios')
        peso_total = sum(
            max(n['puntos'] for n in c['niveles'])
            for c in criterios_data
        )
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.tipo = validated_data.get('tipo', instance.tipo)
        instance.peso_total = peso_total
        instance.save()

        instance.criterios.all().delete()

        for criterio_data in criterios_data:
            niveles_data = criterio_data.pop('niveles')
            criterio = CriterioRubrica.objects.create(id_rubrica=instance, **criterio_data)
            NivelDesempeno.objects.bulk_create([
                NivelDesempeno(id_criterio=criterio, **nivel_data)
                for nivel_data in niveles_data
            ])
        return instance

    def to_representation(self, instance):
        instance = (
            Rubrica.objects
            .select_related('id_proyecto', 'id_docente')
            .prefetch_related('criterios__niveles', 'criterios__id_rap')
            .get(pk=instance.pk)
        )
        return RubricaSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# HU-24: Evaluacion de entregables
# ---------------------------------------------------------------------------

class CalificacionCriterioSerializer(serializers.ModelSerializer):
    criterio_nombre = serializers.CharField(source='id_criterio.nombre', read_only=True)
    peso_porcentual = serializers.DecimalField(
        source='id_criterio.peso_porcentual',
        max_digits=5,
        decimal_places=2,
        read_only=True,
    )
    nivel_numero = serializers.IntegerField(source='id_nivel_seleccionado.nivel', read_only=True)
    nivel_etiqueta = serializers.CharField(
        source='id_nivel_seleccionado.get_etiqueta_display',
        read_only=True,
    )
    nivel_descripcion = serializers.CharField(
        source='id_nivel_seleccionado.descripcion',
        read_only=True,
    )

    class Meta:
        model = CalificacionCriterio
        fields = [
            'id',
            'id_criterio',
            'criterio_nombre',
            'peso_porcentual',
            'id_nivel_seleccionado',
            'nivel_numero',
            'nivel_etiqueta',
            'nivel_descripcion',
            'puntos_obtenidos',
            'comentario_criterio',
        ]
        read_only_fields = fields


class CalificacionCriterioWriteSerializer(serializers.Serializer):
    id_criterio = serializers.PrimaryKeyRelatedField(queryset=CriterioRubrica.objects.all())
    id_nivel_seleccionado = serializers.PrimaryKeyRelatedField(queryset=NivelDesempeno.objects.all())
    comentario_criterio = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        criterio = attrs['id_criterio']
        nivel = attrs['id_nivel_seleccionado']
        if nivel.id_criterio_id != criterio.pk:
            raise serializers.ValidationError({
                'id_nivel_seleccionado': (
                    f'El nivel {nivel.pk} no pertenece al criterio {criterio.pk}.'
                )
            })
        return attrs


class EvaluacionSerializer(serializers.ModelSerializer):
    calificaciones = CalificacionCriterioSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    rubrica_nombre = serializers.CharField(source='id_rubrica.nombre', read_only=True)
    docente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Evaluacion
        fields = [
            'id',
            'id_entregable',
            'id_rubrica',
            'rubrica_nombre',
            'id_docente',
            'docente_nombre',
            'puntuacion_total',
            'comentario_general',
            'fecha_evaluacion',
            'estado',
            'estado_display',
            'calificaciones',
        ]
        read_only_fields = fields

    def get_docente_nombre(self, obj):
        d = obj.id_docente
        if d is None:
            return None
        return f'{d.nombre} {d.apellido}'


class EvaluacionCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/entregables/<id>/evaluaciones/

    Recibe: id_rubrica, comentario_general y una calificacion por cada
    criterio de la rúbrica (id_criterio + id_nivel_seleccionado).

    Calcula automáticamente:
      puntos_obtenidos  = nivel.puntos  (por calificacion)
      puntuacion_total  = Σ (puntos_obtenidos × criterio.peso_porcentual / 100)

    Validaciones:
      - Cada criterio de la rúbrica debe tener exactamente una calificación.
      - El nivel seleccionado debe pertenecer al criterio indicado.
      - No se aceptan criterios ajenos a la rúbrica seleccionada.
    """
    id_rubrica = serializers.PrimaryKeyRelatedField(queryset=Rubrica.objects.all())
    calificaciones = CalificacionCriterioWriteSerializer(many=True)

    class Meta:
        model = Evaluacion
        fields = ['id_rubrica', 'comentario_general', 'calificaciones']

    def validate_calificaciones(self, value):
        if not value:
            raise serializers.ValidationError(
                'Debe proporcionar al menos una calificación.'
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        rubrica = attrs['id_rubrica']
        calificaciones = attrs['calificaciones']

        criterios_rubrica = set(rubrica.criterios.values_list('id', flat=True))
        criterios_enviados = [c['id_criterio'].pk for c in calificaciones]

        # Detectar duplicados en el payload
        if len(criterios_enviados) != len(set(criterios_enviados)):
            raise serializers.ValidationError({
                'calificaciones': 'No puede haber calificaciones duplicadas para el mismo criterio.'
            })

        criterios_enviados_set = set(criterios_enviados)
        faltantes = criterios_rubrica - criterios_enviados_set
        sobrantes = criterios_enviados_set - criterios_rubrica

        if faltantes or sobrantes:
            msg = 'La evaluación debe cubrir exactamente todos los criterios de la rúbrica.'
            if faltantes:
                msg += f' Criterios faltantes: {sorted(faltantes)}.'
            if sobrantes:
                msg += f' Criterios no pertenecen a esta rúbrica: {sorted(sobrantes)}.'
            raise serializers.ValidationError({'calificaciones': msg})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        calificaciones_data = validated_data.pop('calificaciones')

        # Calcular puntuacion_total ponderada
        total = Decimal('0')
        for cal in calificaciones_data:
            puntos = cal['id_nivel_seleccionado'].puntos
            peso = cal['id_criterio'].peso_porcentual
            total += puntos * peso / Decimal('100')

        evaluacion = Evaluacion.objects.create(
            puntuacion_total=total,
            **validated_data,
        )

        CalificacionCriterio.objects.bulk_create([
            CalificacionCriterio(
                id_evaluacion=evaluacion,
                id_criterio=cal['id_criterio'],
                id_nivel_seleccionado=cal['id_nivel_seleccionado'],
                puntos_obtenidos=cal['id_nivel_seleccionado'].puntos,
                comentario_criterio=cal.get('comentario_criterio') or '',
            )
            for cal in calificaciones_data
        ])

        return evaluacion

    def to_representation(self, instance):
        return EvaluacionSerializer(instance, context=self.context).data


class EvaluacionPublicarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluacion
        fields = ['estado']
        read_only_fields = ['estado']

    def update(self, instance, validated_data):
        instance.estado = Evaluacion.Estado.PUBLICADA
        instance.save(update_fields=['estado'])
        return instance

    def to_representation(self, instance):
        return EvaluacionSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# HU-25: Retroalimentación
# ---------------------------------------------------------------------------

class RetroalimentacionSerializer(serializers.ModelSerializer):
    docente_nombre = serializers.SerializerMethodField()
    destino = serializers.SerializerMethodField()

    class Meta:
        model = Retroalimentacion
        fields = [
            'id',
            'id_proyecto',
            'tipo',
            'contenido',
            'fecha_registro',
            'id_docente',
            'docente_nombre',
            'id_equipo',
            'id_estudiante',
            'id_actividad',
            'destino',
        ]
        read_only_fields = fields

    def get_docente_nombre(self, obj):
        d = obj.id_docente
        if d is None:
            return None
        return f'{d.nombre} {d.apellido}'

    def get_destino(self, obj):
        """Resumen legible del destino según el tipo."""
        if obj.tipo == Retroalimentacion.Tipo.GRUPAL and obj.id_equipo:
            return {'tipo': 'equipo', 'nombre': obj.id_equipo.nombre}
        if obj.tipo == Retroalimentacion.Tipo.INDIVIDUAL and obj.id_estudiante:
            e = obj.id_estudiante
            return {'tipo': 'estudiante', 'nombre': f'{e.nombre} {e.apellido}'}
        if obj.tipo == Retroalimentacion.Tipo.ACTIVIDAD and obj.id_actividad:
            return {'tipo': 'actividad', 'nombre': obj.id_actividad.nombre}
        return None


class RetroalimentacionCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/proyectos/<id>/retroalimentaciones/

    Reglas de tipo:
      grupal     → id_equipo requerido; id_estudiante e id_actividad deben ser nulos.
      individual → id_estudiante requerido; id_equipo e id_actividad deben ser nulos.
      actividad  → id_actividad requerida; id_equipo e id_estudiante deben ser nulos.
    """
    id_equipo = serializers.PrimaryKeyRelatedField(
        queryset=Equipo.objects.all(),
        required=False,
        allow_null=True,
    )
    id_estudiante = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo_rol__in=['estudiante', 'lider_equipo']),
        required=False,
        allow_null=True,
    )
    id_actividad = serializers.PrimaryKeyRelatedField(
        queryset=Actividad.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Retroalimentacion
        fields = ['tipo', 'contenido', 'id_equipo', 'id_estudiante', 'id_actividad']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tipo       = attrs.get('tipo')
        equipo     = attrs.get('id_equipo')
        estudiante = attrs.get('id_estudiante')
        actividad  = attrs.get('id_actividad')

        if tipo == Retroalimentacion.Tipo.GRUPAL:
            if not equipo:
                raise serializers.ValidationError(
                    {'id_equipo': 'Se requiere id_equipo para retroalimentación grupal.'}
                )
            attrs['id_estudiante'] = None
            attrs['id_actividad'] = None

        elif tipo == Retroalimentacion.Tipo.INDIVIDUAL:
            if not estudiante:
                raise serializers.ValidationError(
                    {'id_estudiante': 'Se requiere id_estudiante para retroalimentación individual.'}
                )
            attrs['id_equipo'] = None
            attrs['id_actividad'] = None

        elif tipo == Retroalimentacion.Tipo.ACTIVIDAD:
            if not actividad:
                raise serializers.ValidationError(
                    {'id_actividad': 'Se requiere id_actividad para retroalimentación de actividad.'}
                )
            attrs['id_equipo'] = None
            attrs['id_estudiante'] = None

        return attrs

    def to_representation(self, instance):
        return RetroalimentacionSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# HU-26: Autoevaluación
# ---------------------------------------------------------------------------

class DetalleAutoevaluacionSerializer(serializers.ModelSerializer):
    criterio_nombre = serializers.CharField(source="id_criterio.nombre", read_only=True)
    peso_porcentual = serializers.DecimalField(
        source="id_criterio.peso_porcentual",
        max_digits=5, decimal_places=2, read_only=True,
    )
    nivel_numero   = serializers.IntegerField(source="id_nivel_seleccionado.nivel", read_only=True)
    nivel_etiqueta = serializers.CharField(
        source="id_nivel_seleccionado.get_etiqueta_display", read_only=True,
    )

    class Meta:
        model = DetalleAutoevaluacion
        fields = [
            "id", "id_criterio", "criterio_nombre", "peso_porcentual",
            "id_nivel_seleccionado", "nivel_numero", "nivel_etiqueta",
            "puntos_obtenidos", "comentario",
        ]
        read_only_fields = fields


class DetalleAutoevaluacionWriteSerializer(serializers.Serializer):
    id_criterio           = serializers.PrimaryKeyRelatedField(queryset=CriterioRubrica.objects.all())
    id_nivel_seleccionado = serializers.PrimaryKeyRelatedField(queryset=NivelDesempeno.objects.all())
    comentario            = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        criterio = attrs["id_criterio"]
        nivel    = attrs["id_nivel_seleccionado"]
        if nivel.id_criterio_id != criterio.pk:
            raise serializers.ValidationError({
                "id_nivel_seleccionado": (
                    f"El nivel {nivel.pk} no pertenece al criterio {criterio.pk}."
                )
            })
        return attrs


class AutoevaluacionSerializer(serializers.ModelSerializer):
    detalles          = DetalleAutoevaluacionSerializer(many=True, read_only=True)
    estado_display    = serializers.CharField(source="get_estado_display", read_only=True)
    rubrica_nombre    = serializers.CharField(source="id_rubrica.nombre", read_only=True)
    estudiante_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Autoevaluacion
        fields = [
            "id", "id_proyecto", "id_estudiante", "estudiante_nombre",
            "id_rubrica", "rubrica_nombre",
            "puntuacion_total", "reflexion_texto",
            "fecha_registro", "estado", "estado_display",
            "periodo_evaluacion", "detalles",
        ]
        read_only_fields = fields

    def get_estudiante_nombre(self, obj):
        e = obj.id_estudiante
        if e is None:
            return None
        return f"{e.nombre} {e.apellido}"


class AutoevaluacionCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/proyectos/<id>/autoevaluaciones/

    El estudiante se autoevalua seleccionando un nivel por cada criterio
    de la rubrica indicada (id_estudiante viene de request.user).

    Validaciones:
      - Una sola autoevaluacion por (proyecto, estudiante, periodo_evaluacion).
      - Todos los criterios de la rubrica deben estar cubiertos.
      - El nivel seleccionado debe pertenecer al criterio indicado.

    Calculo automatico:
      puntos_obtenidos = nivel.puntos
      puntuacion_total = Sum(puntos_obtenidos x criterio.peso_porcentual / 100)
    """
    id_rubrica = serializers.PrimaryKeyRelatedField(queryset=Rubrica.objects.all())
    detalles   = DetalleAutoevaluacionWriteSerializer(many=True)

    class Meta:
        model  = Autoevaluacion
        fields = ["id_rubrica", "reflexion_texto", "periodo_evaluacion", "estado", "detalles"]
        extra_kwargs = {"estado": {"required": False}}

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un detalle de autoevaluacion."
            )
        return value

    def validate(self, attrs):
        attrs      = super().validate(attrs)
        rubrica    = attrs["id_rubrica"]
        detalles   = attrs["detalles"]
        periodo    = attrs["periodo_evaluacion"]
        estudiante = self.context["request"].user
        proyecto   = self.context["proyecto"]

        # 1. Unicidad por periodo
        qs = Autoevaluacion.objects.filter(
            id_proyecto=proyecto,
            id_estudiante=estudiante,
            periodo_evaluacion=periodo,
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({
                "periodo_evaluacion": (
                    f"Ya existe una autoevaluacion para el periodo \"{periodo}\" en este proyecto."
                )
            })

        # 2. Cobertura exacta de criterios sin duplicados
        criterios_rubrica  = set(rubrica.criterios.values_list("id", flat=True))
        criterios_enviados = [d["id_criterio"].pk for d in detalles]

        if len(criterios_enviados) != len(set(criterios_enviados)):
            raise serializers.ValidationError({
                "detalles": "No puede haber detalles duplicados para el mismo criterio."
            })

        criterios_set = set(criterios_enviados)
        faltantes = criterios_rubrica - criterios_set
        sobrantes = criterios_set - criterios_rubrica
        if faltantes or sobrantes:
            msg = "La autoevaluacion debe cubrir exactamente todos los criterios de la rubrica."
            if faltantes:
                msg += f" Criterios faltantes: {sorted(faltantes)}."
            if sobrantes:
                msg += f" Criterios ajenos a la rubrica: {sorted(sobrantes)}."
            raise serializers.ValidationError({"detalles": msg})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        proyecto      = self.context["proyecto"]
        estudiante    = self.context["request"].user

        total = Decimal("0")
        for d in detalles_data:
            total += d["id_nivel_seleccionado"].puntos * d["id_criterio"].peso_porcentual / Decimal("100")

        autoevaluacion = Autoevaluacion.objects.create(
            id_proyecto=proyecto,
            id_estudiante=estudiante,
            puntuacion_total=total,
            **validated_data,
        )

        DetalleAutoevaluacion.objects.bulk_create([
            DetalleAutoevaluacion(
                id_autoevaluacion=autoevaluacion,
                id_criterio=d["id_criterio"],
                id_nivel_seleccionado=d["id_nivel_seleccionado"],
                puntos_obtenidos=d["id_nivel_seleccionado"].puntos,
                comentario=d.get("comentario") or "",
            )
            for d in detalles_data
        ])

        return autoevaluacion

    def to_representation(self, instance):
        return AutoevaluacionSerializer(instance, context=self.context).data


class AutoevaluacionHU26CreateSerializer(serializers.Serializer):
    """
    POST /api/proyectos/<proyecto_id>/autoevaluaciones/ (HU-26 BE-02)
    Valida estructura del body. Período, unicidad y pertenencia se validan en la vista.
    """
    id_rubrica = serializers.PrimaryKeyRelatedField(queryset=Rubrica.objects.all())
    reflexion_texto = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    detalles = DetalleAutoevaluacionWriteSerializer(many=True)

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError(
                'Debe proporcionar al menos un detalle de autoevaluación.'
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        rubrica = attrs['id_rubrica']
        detalles = attrs['detalles']

        criterios_rubrica = set(rubrica.criterios.values_list('id', flat=True))
        criterios_enviados = [d['id_criterio'].pk for d in detalles]

        if len(criterios_enviados) != len(set(criterios_enviados)):
            raise serializers.ValidationError({
                'detalles': 'No puede haber detalles duplicados para el mismo criterio.'
            })

        criterios_set = set(criterios_enviados)
        faltantes = criterios_rubrica - criterios_set
        sobrantes = criterios_set - criterios_rubrica
        if faltantes or sobrantes:
            msg = 'La autoevaluación debe cubrir exactamente todos los criterios de la rúbrica.'
            if faltantes:
                msg += f' Criterios faltantes: {sorted(faltantes)}.'
            if sobrantes:
                msg += f' Criterios ajenos a la rúbrica: {sorted(sobrantes)}.'
            raise serializers.ValidationError({'detalles': msg})

        return attrs


class AutoevaluacionConComparativoSerializer(serializers.ModelSerializer):
    """
    GET /api/proyectos/<proyecto_id>/autoevaluaciones/mia/ (HU-26 BE-03)
    Incluye detalles y comparativo con la evaluación del docente (si existe).
    Requiere 'proyecto_id' en context.
    """
    detalles = DetalleAutoevaluacionSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    rubrica_nombre = serializers.CharField(source='id_rubrica.nombre', read_only=True)
    estudiante_nombre = serializers.SerializerMethodField()
    evaluacion_docente = serializers.SerializerMethodField()

    class Meta:
        model = Autoevaluacion
        fields = [
            'id', 'id_proyecto', 'id_estudiante', 'estudiante_nombre',
            'id_rubrica', 'rubrica_nombre',
            'puntuacion_total', 'reflexion_texto',
            'fecha_registro', 'estado', 'estado_display',
            'periodo_evaluacion', 'detalles', 'evaluacion_docente',
        ]
        read_only_fields = fields

    def get_estudiante_nombre(self, obj):
        e = obj.id_estudiante
        if e is None:
            return None
        return f'{e.nombre} {e.apellido}'

    def get_evaluacion_docente(self, obj):
        proyecto_id = self.context.get('proyecto_id')
        eval_doc = (
            Evaluacion.objects
            .filter(
                id_rubrica=obj.id_rubrica,
                id_entregable__id_actividad__id_fase__id_proyecto_id=proyecto_id,
            )
            .order_by('-fecha_evaluacion')
            .first()
        )
        if eval_doc is None:
            return None
        return {
            'id': eval_doc.pk,
            'puntuacion_total': eval_doc.puntuacion_total,
            'comentario_general': eval_doc.comentario_general,
        }


# ---------------------------------------------------------------------------
# HU-27: Coevaluación
# ---------------------------------------------------------------------------

class DetalleCoevaluacionSerializer(serializers.ModelSerializer):
    criterio_nombre = serializers.CharField(source="id_criterio.nombre", read_only=True)
    peso_porcentual = serializers.DecimalField(
        source="id_criterio.peso_porcentual",
        max_digits=5, decimal_places=2, read_only=True,
    )
    nivel_numero   = serializers.IntegerField(source="id_nivel_seleccionado.nivel", read_only=True)
    nivel_etiqueta = serializers.CharField(
        source="id_nivel_seleccionado.get_etiqueta_display", read_only=True,
    )

    class Meta:
        model = DetalleCoevaluacion
        fields = [
            "id", "id_criterio", "criterio_nombre", "peso_porcentual",
            "id_nivel_seleccionado", "nivel_numero", "nivel_etiqueta",
            "puntos_obtenidos", "comentario",
        ]
        read_only_fields = fields


class DetalleCoevaluacionWriteSerializer(serializers.Serializer):
    id_criterio           = serializers.PrimaryKeyRelatedField(queryset=CriterioRubrica.objects.all())
    id_nivel_seleccionado = serializers.PrimaryKeyRelatedField(queryset=NivelDesempeno.objects.all())
    comentario            = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        criterio = attrs["id_criterio"]
        nivel    = attrs["id_nivel_seleccionado"]
        if nivel.id_criterio_id != criterio.pk:
            raise serializers.ValidationError({
                "id_nivel_seleccionado": (
                    f"El nivel {nivel.pk} no pertenece al criterio {criterio.pk}."
                )
            })
        return attrs


class CoevaluacionSerializer(serializers.ModelSerializer):
    detalles         = DetalleCoevaluacionSerializer(many=True, read_only=True)
    estado_display   = serializers.CharField(source="get_estado_display", read_only=True)
    rubrica_nombre   = serializers.CharField(source="id_rubrica.nombre", read_only=True)
    evaluador_nombre = serializers.SerializerMethodField()
    evaluado_nombre  = serializers.SerializerMethodField()

    class Meta:
        model = Coevaluacion
        fields = [
            "id", "id_proyecto",
            "id_evaluador", "evaluador_nombre",
            "id_evaluado", "evaluado_nombre",
            "id_rubrica", "rubrica_nombre",
            "puntuacion_total", "comentario",
            "fecha_registro", "estado", "estado_display",
            "periodo_evaluacion", "detalles",
        ]
        read_only_fields = fields

    def get_evaluador_nombre(self, obj):
        e = obj.id_evaluador
        if e is None:
            return None
        return f"{e.nombre} {e.apellido}"

    def get_evaluado_nombre(self, obj):
        e = obj.id_evaluado
        if e is None:
            return None
        return f"{e.nombre} {e.apellido}"


class CoevaluacionCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/proyectos/<id>/coevaluaciones/

    El evaluador (request.user) coevalúa a id_evaluado seleccionando un nivel
    por cada criterio de la rúbrica. Validaciones:
      - evaluador ≠ evaluado.
      - Ambos pertenecen al mismo equipo activo del proyecto.
      - Solo una coevaluación por (evaluador, evaluado, periodo_evaluacion).
      - Cobertura exacta de criterios de la rúbrica sin duplicados.
    """
    id_evaluado = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo_rol__in=["estudiante", "lider_equipo"])
    )
    id_rubrica = serializers.PrimaryKeyRelatedField(queryset=Rubrica.objects.all())
    detalles   = DetalleCoevaluacionWriteSerializer(many=True)

    class Meta:
        model  = Coevaluacion
        fields = ["id_evaluado", "id_rubrica", "comentario", "periodo_evaluacion", "estado", "detalles"]
        extra_kwargs = {"estado": {"required": False}}

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un detalle de coevaluación."
            )
        return value

    def validate(self, attrs):
        from apps.equipos.models import MiembroEquipo

        attrs     = super().validate(attrs)
        evaluador = self.context["request"].user
        evaluado  = attrs["id_evaluado"]
        rubrica   = attrs["id_rubrica"]
        detalles  = attrs["detalles"]
        periodo   = attrs["periodo_evaluacion"]
        proyecto  = self.context["proyecto"]

        # 1. Evaluador ≠ evaluado
        if evaluador.pk == evaluado.pk:
            raise serializers.ValidationError(
                {"id_evaluado": "No puedes evaluarte a ti mismo."}
            )

        # 2. Ambos deben pertenecer al mismo equipo activo del proyecto
        equipos_evaluador = set(
            MiembroEquipo.objects.filter(
                equipo__proyecto=proyecto,
                usuario=evaluador,
                estado="activo",
            ).values_list("equipo_id", flat=True)
        )
        equipos_evaluado = set(
            MiembroEquipo.objects.filter(
                equipo__proyecto=proyecto,
                usuario=evaluado,
                estado="activo",
            ).values_list("equipo_id", flat=True)
        )
        if not (equipos_evaluador & equipos_evaluado):
            raise serializers.ValidationError(
                {"id_evaluado": "El estudiante evaluado no pertenece al mismo equipo activo que tú."}
            )

        # 3. Unicidad por (evaluador, evaluado, periodo)
        qs = Coevaluacion.objects.filter(
            id_evaluador=evaluador,
            id_evaluado=evaluado,
            periodo_evaluacion=periodo,
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({
                "periodo_evaluacion": (
                    f"Ya existe una coevaluación para este evaluado en el periodo \"{periodo}\"."
                )
            })

        # 4. Cobertura exacta de criterios sin duplicados
        criterios_rubrica  = set(rubrica.criterios.values_list("id", flat=True))
        criterios_enviados = [d["id_criterio"].pk for d in detalles]

        if len(criterios_enviados) != len(set(criterios_enviados)):
            raise serializers.ValidationError({
                "detalles": "No puede haber detalles duplicados para el mismo criterio."
            })

        criterios_set = set(criterios_enviados)
        faltantes = criterios_rubrica - criterios_set
        sobrantes = criterios_set - criterios_rubrica
        if faltantes or sobrantes:
            msg = "La coevaluación debe cubrir exactamente todos los criterios de la rúbrica."
            if faltantes:
                msg += f" Criterios faltantes: {sorted(faltantes)}."
            if sobrantes:
                msg += f" Criterios ajenos a la rúbrica: {sorted(sobrantes)}."
            raise serializers.ValidationError({"detalles": msg})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        proyecto      = self.context["proyecto"]
        evaluador     = self.context["request"].user

        total = Decimal("0")
        for d in detalles_data:
            total += d["id_nivel_seleccionado"].puntos * d["id_criterio"].peso_porcentual / Decimal("100")

        coevaluacion = Coevaluacion.objects.create(
            id_proyecto=proyecto,
            id_evaluador=evaluador,
            puntuacion_total=total,
            **validated_data,
        )

        DetalleCoevaluacion.objects.bulk_create([
            DetalleCoevaluacion(
                id_coevaluacion=coevaluacion,
                id_criterio=d["id_criterio"],
                id_nivel_seleccionado=d["id_nivel_seleccionado"],
                puntos_obtenidos=d["id_nivel_seleccionado"].puntos,
                comentario=d.get("comentario") or "",
            )
            for d in detalles_data
        ])

        return coevaluacion

    def to_representation(self, instance):
        return CoevaluacionSerializer(instance, context=self.context).data
