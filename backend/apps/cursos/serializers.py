from rest_framework import serializers

from apps.configuracion.models import PeriodoAcademico
from .models import Curso, Proyecto


# ---------------------------------------------------------------------------
# Curso
# ---------------------------------------------------------------------------

class CursoSerializer(serializers.ModelSerializer):
    docente_nombre = serializers.SerializerMethodField()
    periodo_nombre = serializers.SerializerMethodField()
    total_proyectos = serializers.SerializerMethodField()
    total_equipos = serializers.SerializerMethodField()

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
            'total_proyectos',
            'total_equipos',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = [
            'id',
            'id_docente',
            'estado',
            'total_proyectos',
            'total_equipos',
            'fecha_creacion',
            'fecha_actualizacion',
        ]

    def get_docente_nombre(self, obj):
        d = obj.id_docente
        return f'{d.nombre} {d.apellido}'

    def get_periodo_nombre(self, obj):
        return obj.id_periodo_academico.nombre

    def get_total_proyectos(self, obj):
        # len() aprovecha el prefetch cache de 'proyectos'
        return len(obj.proyectos.all())

    def get_total_equipos(self, obj):
        # Suma equipos de todos los proyectos; len() usa prefetch 'proyectos__equipos'
        return sum(len(p.equipos.all()) for p in obj.proyectos.all())

    def validate_id_periodo_academico(self, periodo):
        if periodo.estado != PeriodoAcademico.Estado.ACTIVO:
            raise serializers.ValidationError(
                'El período académico debe estar activo.'
            )
        return periodo

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if self.instance is not None and request is not None:
            if self.instance.id_docente_id != request.user.pk:
                raise serializers.ValidationError(
                    'Solo el docente propietario puede modificar este curso.'
                )
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['id_docente'] = request.user
        validated_data['usuario_creo'] = request.user
        return super().create(validated_data)


class CursoUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para PUT/PATCH: solo nombre, descripcion y estado."""

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

    total_equipos = serializers.SerializerMethodField()

    class Meta:
        model = Proyecto
        fields = [
            'id',
            'id_curso',
            'nombre',
            'descripcion',
            'estado',
            'fecha_inicio',
            'fecha_fin_estimada',
            'fecha_creacion',
            'total_equipos',
        ]
        read_only_fields = fields  # completamente de lectura; escritura via Create/Update

    def get_total_equipos(self, obj):
        return len(obj.equipos.all())


class ProyectoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de creación. El id_curso lo inyecta la vista desde la URL.
    El docente solo envía: nombre, descripcion, fecha_inicio, fecha_fin_estimada.
    El estado arranca siempre en 'planificado' (default del modelo).
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