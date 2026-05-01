from rest_framework import serializers

from apps.configuracion.models import PeriodoAcademico
from apps.usuarios.models import Usuario
from apps.equipos.serializers import EquipoDetalleSerializer
from .models import Curso, ObjetivoProyecto, Proyecto


# ---------------------------------------------------------------------------
# Curso
# ---------------------------------------------------------------------------

class CursoSerializer(serializers.ModelSerializer):
    """Serializer de lectura para cursos (docente y admin)."""
    docente_nombre = serializers.SerializerMethodField()
    periodo_nombre = serializers.SerializerMethodField()
    total_proyectos = serializers.SerializerMethodField()
    total_equipos = serializers.SerializerMethodField()
    cantidad_estudiantes_actual = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            'id',
            'nombre',
            'descripcion',
            'codigo',
            'id_docente',
            'docente_nombre',
            'id_periodo_academico',
            'periodo_nombre',
            'estado',
            'cantidad_max_estudiantes',
            'cantidad_estudiantes_actual',
            'total_proyectos',
            'total_equipos',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = fields

    def get_docente_nombre(self, obj):
        d = obj.id_docente
        return f'{d.nombre} {d.apellido}'

    def get_periodo_nombre(self, obj):
        return obj.id_periodo_academico.nombre

    def get_total_proyectos(self, obj):
        return len(obj.proyectos.all())

    def get_total_equipos(self, obj):
        return sum(len(p.equipos.all()) for p in obj.proyectos.all())

    def get_cantidad_estudiantes_actual(self, obj):
        from apps.equipos.models import MiembroEquipo
        return MiembroEquipo.objects.filter(
            equipo__proyecto__id_curso=obj,
            estado='activo',
        ).count()


class CursoAdminCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para que el admin cree un curso."""
    id_periodo_academico = serializers.PrimaryKeyRelatedField(
        queryset=PeriodoAcademico.objects.all(),
    )
    id_docente = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo_rol='docente'),
    )

    class Meta:
        model = Curso
        fields = [
            'nombre',
            'codigo',
            'descripcion',
            'id_periodo_academico',
            'id_docente',
            'cantidad_max_estudiantes',
        ]

    def validate_id_periodo_academico(self, periodo):
        if periodo.estado != PeriodoAcademico.Estado.ACTIVO:
            raise serializers.ValidationError('El período académico debe estar activo.')
        return periodo

    def create(self, validated_data):
        validated_data['usuario_creo'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        return CursoSerializer(instance, context=self.context).data


class CursoAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para que el admin edite cualquier campo del curso."""
    id_periodo_academico = serializers.PrimaryKeyRelatedField(
        queryset=PeriodoAcademico.objects.all(),
        required=False,
    )
    id_docente = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo_rol='docente'),
        required=False,
    )

    class Meta:
        model = Curso
        fields = [
            'nombre',
            'codigo',
            'descripcion',
            'estado',
            'id_periodo_academico',
            'id_docente',
            'cantidad_max_estudiantes',
        ]

    def to_representation(self, instance):
        return CursoSerializer(instance, context=self.context).data


class CursoUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para que el docente edite su propio curso."""

    class Meta:
        model = Curso
        fields = ['nombre', 'descripcion', 'estado']

    def to_representation(self, instance):
        return CursoSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# Proyecto
# ---------------------------------------------------------------------------

def _validate_fechas(attrs, instance=None):
    """Valida que fecha_fin_estimada >= fecha_inicio."""
    fecha_inicio = attrs.get('fecha_inicio') or getattr(instance, 'fecha_inicio', None)
    fecha_fin = attrs.get('fecha_fin_estimada') or getattr(instance, 'fecha_fin_estimada', None)
    if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
        raise serializers.ValidationError(
            {'fecha_fin_estimada': 'La fecha fin estimada no puede ser anterior a la fecha de inicio.'}
        )


class ProyectoSerializer(serializers.ModelSerializer):
    """Serializer de lectura. id_curso se incluye como FK numérica."""
    fecha_fin = serializers.DateField(source='fecha_fin_estimada')
    cantidad_equipos = serializers.SerializerMethodField()
    equipo = serializers.SerializerMethodField()

    class Meta:
        model = Proyecto
        fields = [
            'id',
            'id_curso',
            'nombre',
            'descripcion',
            'estado',
            'fecha_inicio',
            'fecha_fin',
            'cantidad_equipos',
            'equipo',
            'fecha_creacion',
        ]
        read_only_fields = fields

    def get_cantidad_equipos(self, obj):
        return len(obj.equipos.all())

    def get_equipo(self, obj):
        equipo = obj.equipos.filter(estado='activo').first()
        if not equipo:
            return None
        return EquipoDetalleSerializer(equipo).data


class ProyectoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de creación. El id_curso lo inyecta la vista desde la URL.
    El docente solo envía: nombre, descripcion, fecha_inicio, fecha_fin_estimada.
    """

    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin_estimada']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        _validate_fechas(attrs)
        return attrs

    def to_representation(self, instance):
        return ProyectoSerializer(instance, context=self.context).data


class ProyectoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer de actualización (PUT/PATCH).
    Permite cambiar nombre, descripcion, estado y fechas.
    id_curso no es modificable.
    """

    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'estado', 'fecha_inicio', 'fecha_fin_estimada']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        _validate_fechas(attrs, instance=self.instance)
        return attrs

    def to_representation(self, instance):
        return ProyectoSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# Objetivo
# ---------------------------------------------------------------------------

class ObjetivoListSerializer(serializers.ListSerializer):
    """
    ListSerializer personalizado para creación en lote de objetivos.

    DRF llama a este serializer automáticamente cuando se instancia
    ObjetivoSerializer con many=True.  Sobreescribe create() para usar
    bulk_create(), que emite una sola INSERT con todas las filas en lugar
    de N inserciones individuales.
    """

    def create(self, validated_data):
        # Construye los objetos en memoria sin tocar la BD todavía.
        objetivos = [ObjetivoProyecto(**item) for item in validated_data]
        # Una sola INSERT para todo el lote; más eficiente que save() por fila.
        return ObjetivoProyecto.objects.bulk_create(objetivos)


class ObjetivoSerializer(serializers.ModelSerializer):
    """
    Serializer para ObjetivoProyecto.

    Uso individual (un solo objetivo):
        ObjetivoSerializer(data=request.data, context={'request': request})

    Uso en lote (lista de objetivos en un request):
        ObjetivoSerializer(data=request.data, many=True, context={'request': request})
        → DRF selecciona ObjetivoListSerializer como ListSerializer automáticamente.

    El campo id_proyecto es de solo lectura; la vista lo inyecta desde la URL
    con serializer.save(id_proyecto=proyecto).
    """

    class Meta:
        model = ObjetivoProyecto
        fields = [
            'id',
            'id_proyecto',
            'descripcion',
            'tipo',
            'orden',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'id_proyecto', 'fecha_creacion']
        # Asocia este serializer con ObjetivoListSerializer para el caso many=True.
        list_serializer_class = ObjetivoListSerializer

    def validate_tipo(self, value):
        """Rechaza valores que no estén en las opciones definidas en el modelo."""
        tipos_validos = ObjetivoProyecto.Tipo.values  # ['general', 'especifico']
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f'Tipo inválido. Debe ser uno de: {tipos_validos}.'
            )
        return value

    def validate_orden(self, value):
        """El orden debe ser un entero positivo (≥ 1)."""
        if value < 1:
            raise serializers.ValidationError(
                'El orden debe ser un número positivo (mínimo 1).'
            )
        return value

    def validate(self, attrs):
        """
        Valida unicidad de orden dentro del proyecto en actualizaciones.
        En creación la constraint de BD actúa como segunda línea de defensa,
        ya que id_proyecto aún no está en attrs (se inyecta en save()).
        """
        attrs = super().validate(attrs)

        if self.instance is not None:
            orden = attrs.get('orden', self.instance.orden)
            proyecto = self.instance.id_proyecto
            duplicado = (
                ObjetivoProyecto.objects
                .filter(id_proyecto=proyecto, orden=orden)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if duplicado:
                raise serializers.ValidationError(
                    {'orden': f'Ya existe un objetivo con orden {orden} en este proyecto.'}
                )

        return attrs


class ObjetivoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer de escritura para PUT/PATCH de un objetivo individual.

    Campos editables: descripcion, tipo, orden.
    El campo id_proyecto no se puede cambiar (el objetivo no se reasigna).

    La respuesta siempre devuelve la representación completa via
    ObjetivoSerializer para que el cliente reciba el objeto actualizado
    con todos sus campos de solo lectura (id, fecha_creacion, etc.).
    """

    class Meta:
        model = ObjetivoProyecto
        fields = ['descripcion', 'tipo', 'orden']

    def validate_orden(self, value):
        """El orden debe ser entero positivo (≥ 1)."""
        if value < 1:
            raise serializers.ValidationError(
                'El orden debe ser un número positivo (mínimo 1).'
            )
        return value

    def validate(self, attrs):
        """
        Verifica que el nuevo orden no colisione con otro objetivo
        del mismo proyecto.  Solo aplica en actualizaciones (self.instance existe).
        """
        attrs = super().validate(attrs)

        if self.instance is not None:
            # Usa el nuevo valor de orden si fue enviado; si no, el actual.
            orden = attrs.get('orden', self.instance.orden)
            duplicado = (
                ObjetivoProyecto.objects
                .filter(id_proyecto=self.instance.id_proyecto, orden=orden)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if duplicado:
                raise serializers.ValidationError(
                    {'orden': f'Ya existe un objetivo con orden {orden} en este proyecto.'}
                )

        return attrs

    def to_representation(self, instance):
        # Devuelve la representación completa del objetivo actualizado.
        return ObjetivoSerializer(instance, context=self.context).data
