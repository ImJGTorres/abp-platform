from rest_framework import serializers

from apps.configuracion.models import PeriodoAcademico
from apps.usuarios.models import Usuario
from apps.equipos.models import Equipo, MiembroEquipo
from apps.equipos.serializers import EquipoDetalleSerializer
from .models import Actividad, AvanceActividad, Curso, FaseProyecto, HitoProyecto, ObjetivoProyecto, Proyecto


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
        return obj.id_periodo_academico.nombre if obj.id_periodo_academico else ''

    def get_total_proyectos(self, obj):
        return len(obj.proyectos.all())

    def get_total_equipos(self, obj):
        return sum(len(p.equipos.all()) for p in obj.proyectos.all())

    def get_cantidad_estudiantes_actual(self, obj):
        from apps.equipos.models import Equipo, MiembroEquipo
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
    porcentaje_progreso = serializers.SerializerMethodField()
    total_fases = serializers.SerializerMethodField()
    total_actividades = serializers.SerializerMethodField()
    actividades_completadas = serializers.SerializerMethodField()
    periodo_academico_id = serializers.IntegerField(
        source='id_curso.id_periodo_academico_id',
        read_only=True,
        default=None,
    )
    periodo_academico_nombre = serializers.CharField(
        source='id_curso.id_periodo_academico.nombre',
        read_only=True,
        default='',
    )

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
            'porcentaje_progreso',
            'total_fases',
            'total_actividades',
            'actividades_completadas',
            'fecha_creacion',
            'periodo_academico_id',
            'periodo_academico_nombre',
        ]
        read_only_fields = fields

    def get_cantidad_equipos(self, obj):
        return len(obj.equipos.all())

    def get_equipo(self, obj):
        request = self.context.get('request')
        if request:
            tipo_rol = getattr(request.user, 'tipo_rol', None)
            if tipo_rol in ('estudiante', 'lider_equipo'):
                # Devuelve el equipo al que pertenece el estudiante en este proyecto
                miembro = MiembroEquipo.objects.filter(
                    equipo__proyecto=obj,
                    usuario=request.user,
                    estado='activo',
                ).select_related('equipo').first()
                if miembro:
                    return EquipoDetalleSerializer(miembro.equipo).data
                return None
        # Docente / admin: primer equipo activo
        equipo = obj.equipos.filter(estado='activo').first()
        if not equipo:
            return None
        return EquipoDetalleSerializer(equipo).data

    def get_porcentaje_progreso(self, obj):
        # Usa el valor anotado por ProyectoQuerySet.con_progreso() si está disponible.
        if hasattr(obj, 'porcentaje_progreso'):
            val = obj.porcentaje_progreso
            return val if val is not None else 0
        fases = list(obj.fases.all())
        if not fases:
            return 0
        return round(sum(f.porcentaje_completado for f in fases) / len(fases))

    def get_total_fases(self, obj):
        if hasattr(obj, 'total_fases'):
            return obj.total_fases
        return obj.fases.count()

    def get_total_actividades(self, obj):
        if hasattr(obj, 'total_actividades'):
            return obj.total_actividades
        from .models import Actividad
        return Actividad.objects.filter(id_fase__id_proyecto=obj).count()

    def get_actividades_completadas(self, obj):
        if hasattr(obj, 'actividades_completadas'):
            return obj.actividades_completadas
        from .models import Actividad
        return Actividad.objects.filter(id_fase__id_proyecto=obj, estado='completada').count()


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


# ---------------------------------------------------------------------------
# HitoProyecto
# ---------------------------------------------------------------------------

def _validate_fechas_hito(attrs, instance=None, proyecto=None):
    """Valida que fecha_fin > fecha_inicio y que ambas caigan dentro del rango del proyecto."""
    fecha_inicio = attrs.get('fecha_inicio') or getattr(instance, 'fecha_inicio', None)
    fecha_fin = attrs.get('fecha_fin') or getattr(instance, 'fecha_fin', None)

    if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
        raise serializers.ValidationError(
            {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
        )

    if proyecto is None and instance is not None:
        proyecto = instance.id_proyecto

    if proyecto and fecha_inicio and fecha_inicio < proyecto.fecha_inicio:
        raise serializers.ValidationError(
            {'fecha_inicio': 'La fecha de inicio del hito no puede ser anterior a la del proyecto.'}
        )
    if proyecto and fecha_fin and fecha_fin > proyecto.fecha_fin_estimada:
        raise serializers.ValidationError(
            {'fecha_fin': 'La fecha de fin del hito no puede superar la fecha fin del proyecto.'}
        )


class HitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HitoProyecto
        fields = [
            'id',
            'id_proyecto',
            'nombre',
            'descripcion',
            'fecha_inicio',
            'fecha_fin',
            'tipo',
            'estado',
            'fecha_creacion',
        ]
        read_only_fields = fields


class HitoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HitoProyecto
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'tipo', 'estado']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        proyecto = self.context.get('proyecto')
        _validate_fechas_hito(attrs, proyecto=proyecto)
        return attrs

    def to_representation(self, instance):
        return HitoSerializer(instance, context=self.context).data


class HitoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HitoProyecto
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'tipo', 'estado']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        _validate_fechas_hito(attrs, instance=self.instance)
        return attrs

    def to_representation(self, instance):
        return HitoSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# ResultadoAprendizaje (RAP)
# ---------------------------------------------------------------------------

from .models import Actividad, FaseProyecto, ResultadoAprendizaje


class RapSerializer(serializers.ModelSerializer):
    proyecto = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ResultadoAprendizaje
        fields = ['id', 'proyecto', 'nombre', 'descripcion', 'competencia_asociada', 'porcentaje_evaluacion']


class RapCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoAprendizaje
        fields = ['nombre', 'descripcion', 'competencia_asociada', 'porcentaje_evaluacion']


# ---------------------------------------------------------------------------
# FaseProyecto
# ---------------------------------------------------------------------------

def _validate_fechas_fase(attrs, instance=None, proyecto=None):
    """Valida coherencia interna de fechas y rango respecto al proyecto."""
    fecha_inicio = attrs.get('fecha_inicio') or getattr(instance, 'fecha_inicio', None)
    fecha_fin = attrs.get('fecha_fin') or getattr(instance, 'fecha_fin', None)

    if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
        raise serializers.ValidationError(
            {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
        )

    if proyecto is None and instance is not None:
        proyecto = instance.id_proyecto

    if proyecto and fecha_inicio and fecha_inicio < proyecto.fecha_inicio:
        raise serializers.ValidationError(
            {'fecha_inicio': 'La fecha de inicio de la fase no puede ser anterior a la del proyecto.'}
        )
    if proyecto and fecha_fin and fecha_fin > proyecto.fecha_fin_estimada:
        raise serializers.ValidationError(
            {'fecha_fin': 'La fecha de fin de la fase no puede superar la fecha fin estimada del proyecto.'}
        )


class FaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaseProyecto
        fields = [
            'id',
            'id_proyecto',
            'nombre',
            'descripcion',
            'orden',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'fecha_creacion',
            'porcentaje_completado',
        ]
        read_only_fields = fields


class FaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaseProyecto
        fields = ['nombre', 'descripcion', 'orden', 'fecha_inicio', 'fecha_fin', 'estado']

    def validate_orden(self, value):
        if value < 1:
            raise serializers.ValidationError('El orden debe ser un número positivo (mínimo 1).')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        proyecto = self.context.get('proyecto')
        _validate_fechas_fase(attrs, proyecto=proyecto)
        if proyecto:
            orden = attrs.get('orden')
            if orden and FaseProyecto.objects.filter(id_proyecto=proyecto, orden=orden).exists():
                raise serializers.ValidationError(
                    {'orden': f'Ya existe una fase con orden {orden} en este proyecto.'}
                )
        return attrs

    def to_representation(self, instance):
        return FaseSerializer(instance, context=self.context).data


class FaseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaseProyecto
        fields = ['nombre', 'descripcion', 'orden', 'fecha_inicio', 'fecha_fin', 'estado']

    def validate_orden(self, value):
        if value < 1:
            raise serializers.ValidationError('El orden debe ser un número positivo (mínimo 1).')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        fecha_inicio = attrs.get('fecha_inicio') or getattr(self.instance, 'fecha_inicio', None)
        fecha_fin = attrs.get('fecha_fin') or getattr(self.instance, 'fecha_fin', None)
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )
        if self.instance is not None:
            orden = attrs.get('orden', self.instance.orden)
            duplicado = (
                FaseProyecto.objects
                .filter(id_proyecto=self.instance.id_proyecto, orden=orden)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if duplicado:
                raise serializers.ValidationError(
                    {'orden': f'Ya existe una fase con orden {orden} en este proyecto.'}
                )
        return attrs

    def to_representation(self, instance):
        return FaseSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# Actividad
# ---------------------------------------------------------------------------

def _validate_fecha_limite_actividad(attrs, instance=None, fase=None):
    """Valida que fecha_límite esté dentro del rango de la fase y del proyecto."""
    fecha_limite = attrs.get('fecha_limite') or getattr(instance, 'fecha_limite', None)

    if fase is None and instance is not None:
        fase = instance.id_fase

    if not fase or not fecha_limite:
        return

    if fecha_limite < fase.fecha_inicio:
        raise serializers.ValidationError(
            {'fecha_limite': 'La fecha límite no puede ser anterior a la fecha de inicio de la fase.'}
        )
    if fecha_limite > fase.fecha_fin:
        raise serializers.ValidationError(
            {'fecha_limite': 'La fecha límite no puede superar la fecha de fin de la fase.'}
        )

    proyecto = fase.id_proyecto
    if fecha_limite < proyecto.fecha_inicio:
        raise serializers.ValidationError(
            {'fecha_limite': 'La fecha límite no puede ser anterior a la fecha de inicio del proyecto.'}
        )
    if fecha_limite > proyecto.fecha_fin_estimada:
        raise serializers.ValidationError(
            {'fecha_limite': 'La fecha límite no puede superar la fecha fin estimada del proyecto.'}
        )


class ActividadSerializer(serializers.ModelSerializer):
    responsables = serializers.SerializerMethodField()

    def get_responsables(self, obj):
        return [
            {
                'id': u.pk,
                'nombre': u.nombre,
                'apellido': u.apellido,
                'foto_perfil': u.foto_perfil or None,
            }
            for u in obj.responsables.all()
        ]

    class Meta:
        model = Actividad
        fields = [
            'id',
            'id_fase',
            'nombre',
            'descripcion',
            'fecha_limite',
            'prioridad',
            'estado',
            'fecha_creacion',
            'id_responsable',
            'id_equipo_asignado',
            'responsables',
        ]
        read_only_fields = [
            'id', 'id_fase', 'nombre', 'descripcion', 'fecha_limite',
            'prioridad', 'estado', 'fecha_creacion', 'id_responsable', 'id_equipo_asignado',
        ]


def _validate_responsables_equipo(equipo, responsables):
    if not responsables:
        return
    if not equipo:
        raise serializers.ValidationError(
            {'responsables': 'Debe asignar un equipo antes de seleccionar responsables.'}
        )
    miembros_activos = set(
        MiembroEquipo.objects.filter(equipo=equipo, estado='activo').values_list('usuario_id', flat=True)
    )
    no_miembros = [u.pk for u in responsables if u.pk not in miembros_activos]
    if no_miembros:
        raise serializers.ValidationError(
            {'responsables': f'Los siguientes usuarios no son miembros activos del equipo: {no_miembros}'}
        )


class ActividadCreateSerializer(serializers.ModelSerializer):
    id_equipo_asignado = serializers.PrimaryKeyRelatedField(
        queryset=Equipo.objects.all(),
        required=False,
        allow_null=True,
    )
    responsables = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Actividad
        fields = ['nombre', 'descripcion', 'fecha_limite', 'prioridad', 'estado', 'id_equipo_asignado', 'responsables']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        _validate_fecha_limite_actividad(attrs, fase=self.context.get('fase'))
        _validate_responsables_equipo(attrs.get('id_equipo_asignado'), attrs.get('responsables'))
        return attrs

    def create(self, validated_data):
        responsables = validated_data.pop('responsables', None)
        instance = super().create(validated_data)
        if responsables:
            instance.responsables.set(responsables)
        return instance

    def to_representation(self, instance):
        return ActividadSerializer(instance, context=self.context).data


class ActividadUpdateSerializer(serializers.ModelSerializer):
    id_equipo_asignado = serializers.PrimaryKeyRelatedField(
        queryset=Equipo.objects.all(),
        required=False,
        allow_null=True,
    )
    responsables = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Actividad
        fields = ['nombre', 'descripcion', 'fecha_limite', 'prioridad', 'estado', 'id_equipo_asignado', 'responsables']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        _validate_fecha_limite_actividad(attrs, instance=self.instance)
        equipo = attrs.get('id_equipo_asignado', getattr(self.instance, 'id_equipo_asignado', None))
        _validate_responsables_equipo(equipo, attrs.get('responsables'))
        return attrs

    def update(self, instance, validated_data):
        responsables = validated_data.pop('responsables', None)
        instance = super().update(instance, validated_data)
        if responsables is not None:
            instance.responsables.set(responsables)
        if instance.id_equipo_asignado is None:
            instance.responsables.clear()
        return instance

    def to_representation(self, instance):
        return ActividadSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# AvanceActividad
# ---------------------------------------------------------------------------

class AvanceActividadSerializer(serializers.ModelSerializer):
    autor = serializers.SerializerMethodField()

    class Meta:
        model = AvanceActividad
        fields = [
            'id',
            'id_actividad',
            'id_usuario',
            'autor',
            'descripcion',
            'porcentaje_completado',
            'fecha_registro',
            'tipo',
            'url_referencia',
        ]
        read_only_fields = fields

    def get_autor(self, obj):
        u = obj.id_usuario
        if u is None:
            return None
        return {'id': u.pk, 'nombre': u.nombre, 'apellido': u.apellido}


class AvanceActividadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvanceActividad
        fields = ['descripcion', 'porcentaje_completado', 'tipo', 'url_referencia']

    def validate_porcentaje_completado(self, value):
        if not (0 <= value <= 100):
            raise serializers.ValidationError('El porcentaje debe estar entre 0 y 100.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if attrs.get('tipo') == AvanceActividad.Tipo.ENLACE and not attrs.get('url_referencia'):
            raise serializers.ValidationError(
                {'url_referencia': 'Se requiere una URL cuando el tipo es "enlace".'}
            )

        actividad = self.context['actividad']
        usuario = self.context['request'].user

        es_responsable = (
            actividad.id_responsable_id is not None
            and actividad.id_responsable_id == usuario.pk
        )
        if not es_responsable:
            equipo = actividad.id_equipo_asignado
            if equipo is None:
                raise serializers.ValidationError(
                    'Solo el responsable o un miembro del equipo asignado puede registrar avances.'
                )
            es_miembro = MiembroEquipo.objects.filter(
                equipo=equipo,
                usuario=usuario,
                estado='activo',
            ).exists()
            if not es_miembro:
                raise serializers.ValidationError(
                    'Solo el responsable o un miembro activo del equipo asignado puede registrar avances.'
                )

        return attrs

    def to_representation(self, instance):
        return AvanceActividadSerializer(instance, context=self.context).data


class ActividadAsignarResponsableSerializer(serializers.ModelSerializer):
    """PATCH exclusivo para líderes de equipo: asignar id_responsable."""

    class Meta:
        model = Actividad
        fields = ['id_responsable']

    def validate_id_responsable(self, usuario):
        actividad = self.instance
        equipo = actividad.id_equipo_asignado
        if equipo is None:
            raise serializers.ValidationError(
                'La actividad no tiene un equipo asignado.'
            )
        es_miembro = MiembroEquipo.objects.filter(
            equipo=equipo,
            usuario=usuario,
            estado='activo',
        ).exists()
        if not es_miembro:
            raise serializers.ValidationError(
                'El responsable debe ser un miembro activo del equipo asignado a esta actividad.'
            )
        return usuario

    def to_representation(self, instance):
        return ActividadSerializer(instance, context=self.context).data


class ActividadAsignarSerializer(serializers.Serializer):
    """
    PATCH /api/actividades/<pk>/asignar/
    Líder de equipo asigna uno o más responsables a la actividad.
    Todos deben ser miembros activos del equipo asignado.
    """

    responsables = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def validate(self, attrs):
        actividad = self.context['actividad']
        equipo = actividad.id_equipo_asignado
        if equipo is None:
            raise serializers.ValidationError(
                {'responsables': 'La actividad no tiene un equipo asignado.'}
            )
        ids = attrs['responsables']
        if not ids:
            return attrs
        miembros_activos = set(
            MiembroEquipo.objects
            .filter(equipo=equipo, estado='activo')
            .values_list('usuario_id', flat=True)
        )
        no_miembros = [uid for uid in ids if uid not in miembros_activos]
        if no_miembros:
            raise serializers.ValidationError(
                {'responsables': f'Los siguientes usuarios no son miembros activos del equipo: {no_miembros}'}
            )
        return attrs


class ActividadPorEquipoSerializer(serializers.ModelSerializer):
    """Serializer para listar actividades de un equipo con sus responsables."""

    es_responsable           = serializers.SerializerMethodField()
    fase_nombre              = serializers.SerializerMethodField()
    fase_orden               = serializers.SerializerMethodField()
    responsables_detalle     = serializers.SerializerMethodField()
    ultimo_porcentaje_avance = serializers.SerializerMethodField()

    class Meta:
        model = Actividad
        fields = [
            'id', 'id_fase', 'fase_nombre', 'fase_orden',
            'nombre', 'descripcion', 'fecha_limite', 'prioridad',
            'estado', 'fecha_creacion', 'id_responsable',
            'id_equipo_asignado', 'responsables',
            'responsables_detalle', 'es_responsable',
            'ultimo_porcentaje_avance',
        ]
        read_only_fields = fields

    def get_es_responsable(self, obj):
        usuario = self.context['request'].user
        return obj.responsables.filter(pk=usuario.pk).exists()

    def get_fase_nombre(self, obj):
        return obj.id_fase.nombre if obj.id_fase else None

    def get_fase_orden(self, obj):
        return obj.id_fase.orden if obj.id_fase else 0

    def get_responsables_detalle(self, obj):
        return [
            {'id': u.pk, 'nombre': u.nombre, 'apellido': u.apellido}
            for u in obj.responsables.all()
        ]

    def get_ultimo_porcentaje_avance(self, obj):
        cache = getattr(obj, '_prefetched_objects_cache', {})
        avances = cache.get('avances')
        if avances is not None:
            return avances[0].porcentaje_completado if avances else 0
        ultimo = obj.avances.order_by('-fecha_registro').first()
        return ultimo.porcentaje_completado if ultimo else 0
