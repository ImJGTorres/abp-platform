from rest_framework import serializers

from apps.configuracion.models import PeriodoAcademico
from apps.usuarios.models import Usuario
from .models import Curso, Proyecto


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
        return obj.proyectos.count()

    def get_total_equipos(self, obj):
        from apps.equipos.models import Equipo
        return Equipo.objects.filter(proyecto__id_curso=obj).count()

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


class ProyectoSerializer(serializers.ModelSerializer):
    fecha_fin = serializers.DateField(source='fecha_fin_estimada')
    cantidad_equipos = serializers.SerializerMethodField()

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
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'id_curso', 'fecha_creacion']

    def get_cantidad_equipos(self, obj):
        return obj.equipos.count()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin_estimada = attrs.get('fecha_fin_estimada')
        if fecha_inicio and fecha_fin_estimada and fecha_fin_estimada < fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )
        return attrs