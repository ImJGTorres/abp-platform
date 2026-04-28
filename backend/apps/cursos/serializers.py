from rest_framework import serializers

from apps.configuracion.models import PeriodoAcademico
from apps.equipos.serializers import EquipoDetalleSerializer
from .models import Curso, Proyecto


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
        return obj.proyectos.count()

    def get_total_equipos(self, obj):
        # Sum of equipos across all proyectos
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


class ProyectoSerializer(serializers.ModelSerializer):
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
            'fecha_fin_estimada',
            'fecha_creacion',
            'equipo',
        ]
        read_only_fields = ['fecha_creacion']

    def get_equipo(self, obj):
        equipo = obj.equipos.filter(estado='activo').first()
        if not equipo:
            return None
        return EquipoDetalleSerializer(equipo).data

    def validate(self, attrs):
        attrs = super().validate(attrs)

        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin_estimada = attrs.get('fecha_fin_estimada')
        if fecha_inicio and fecha_fin_estimada and fecha_fin_estimada < fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin_estimada': 'La fecha fin estimada no puede ser anterior a la fecha de inicio.'}
            )

        return attrs

    def validate_id_curso(self, curso):
        request = self.context.get('request')
        if request is None:
            return curso

        usuario = getattr(request, 'user', None)
        if usuario is None or not usuario.is_authenticated:
            raise serializers.ValidationError('Se requiere autenticación.')

        if curso.id_docente_id != usuario.pk:
            raise serializers.ValidationError(
                'Solo el docente propietario del curso puede crear un proyecto en él.'
            )

        # Un curso puede tener múltiples proyectos; en creación verificamos que no exista ninguno si se desea restringir
        # Mientras tanto se permite crear varios; si se quiere limitar, cambiar a validación de cantidad.
        # Actualmente no hay restricción de número máximo de proyectos por curso.

        return curso