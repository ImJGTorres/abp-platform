from rest_framework import serializers

from apps.usuarios.models import Usuario

from .models import Equipo, MiembroEquipo


class EquipoSerializer(serializers.ModelSerializer):
    """Serializador de lectura/escritura para el modelo Equipo.

    El campo proyecto es de solo lectura; se inyecta desde la vista.
    La validación de cupo_maximo se delega al método clean() del modelo.
    """

    proyecto = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Equipo
        fields = '__all__'


class EquipoCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear un equipo. La validación de cupo se delega al modelo."""

    capacidad_maxima = serializers.IntegerField(required=True)

    class Meta:
        model = Equipo
        fields = ['nombre', 'capacidad_maxima']

    def create(self, validated_data):
        capacidad = validated_data.pop('capacidad_maxima')
        proyecto = self.context['proyecto']
        return Equipo.objects.create(proyecto=proyecto, nombre=validated_data['nombre'], cupo_maximo=capacidad)


class EquipoUpdateSerializer(serializers.ModelSerializer):
    """Serializador para actualizar un equipo. La validación de cupo se delega al modelo."""

    capacidad_maxima = serializers.IntegerField(required=False)

    class Meta:
        model = Equipo
        fields = ['nombre', 'capacidad_maxima']

    def update(self, instance, validated_data):
        if 'nombre' in validated_data:
            instance.nombre = validated_data['nombre']
        if 'capacidad_maxima' in validated_data:
            instance.cupo_maximo = validated_data['capacidad_maxima']
        instance.save()
        return instance


class EquipoListSerializer(serializers.ModelSerializer):
    capacidad_maxima = serializers.IntegerField(source='cupo_maximo', read_only=True)
    numero_miembros = serializers.SerializerMethodField()
    cupo_disponible = serializers.SerializerMethodField()

    class Meta:
        model = Equipo
        fields = ['id', 'nombre', 'capacidad_maxima', 'numero_miembros', 'cupo_disponible']

    def get_numero_miembros(self, obj):
        return obj.miembros.filter(estado='activo').count()

    def get_cupo_disponible(self, obj):
        activos = obj.miembros.filter(estado='activo').count()
        return max(0, obj.cupo_maximo - activos)


class MiembroEquipoSerializer(serializers.ModelSerializer):
    """Serializador para membresías de equipo.

    El campo equipo es de solo lectura; se inyecta desde la vista via context.
    Las validaciones de unicidad por proyecto y cupo máximo se delegan al modelo.
    """

    equipo = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MiembroEquipo
        fields = '__all__'


# ── Serializers de lectura (vistas de gestión y asignación) ──────────────────

# Serializer que retorna los miembros de un equipo incluyendo rol_interno y descripción de responsabilidades
# junto con los datos básicos del miembro para las vistas de gestión
class MiembroDetalleSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    iniciales       = serializers.SerializerMethodField()
    correo          = serializers.SerializerMethodField()

    class Meta:
        model  = MiembroEquipo
        fields = [
            'id', 'usuario_id', 'nombre_completo', 'iniciales',
            'correo', 'rol_interno', 'estado', 'fecha_asignacion',
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.usuario.nombre} {obj.usuario.apellido}".strip()

    def get_iniciales(self, obj):
        n = obj.usuario.nombre[:1].upper()   if obj.usuario.nombre   else ''
        a = obj.usuario.apellido[:1].upper() if obj.usuario.apellido else ''
        return n + a

    def get_correo(self, obj):
        return obj.usuario.correo


class EquipoDetalleSerializer(serializers.ModelSerializer):
    miembros             = serializers.SerializerMethodField()
    cantidad_miembros    = serializers.SerializerMethodField()
    cupo_disponible      = serializers.SerializerMethodField()
    lider                = serializers.SerializerMethodField()
    cantidad_entregables = serializers.SerializerMethodField()

    class Meta:
        model  = Equipo
        fields = [
            'id', 'nombre', 'descripcion', 'estado', 'cupo_maximo',
            'miembros', 'cantidad_miembros', 'cupo_disponible', 'lider', 'cantidad_entregables',
        ]

    def get_miembros(self, obj):
        activos = obj.miembros.filter(estado='activo').select_related('usuario')
        return MiembroDetalleSerializer(activos, many=True).data

    def get_cantidad_miembros(self, obj):
        return obj.miembros.filter(estado='activo').count()

    def get_cupo_disponible(self, obj):
        activos = obj.miembros.filter(estado='activo').count()
        return max(0, obj.cupo_maximo - activos)

    def get_lider(self, obj):
        lider = obj.miembros.filter(
            rol_interno='lider', estado='activo'
        ).select_related('usuario').first()
        if not lider:
            return None
        return {
            'id':     lider.usuario.id,
            'nombre': f"{lider.usuario.nombre} {lider.usuario.apellido}".strip(),
        }

    def get_cantidad_entregables(self, obj):
        return 0  # placeholder hasta que se implemente el modelo Entregable


# Serializer para listar usuarios (estudiantes) con información resumida.
# Retorna solo campos básicos: id, nombre, apellido, correo y codigo.
# Utilizado para mostrar estudiantes disponibles para asignación.
class UsuarioResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellido', 'correo', 'codigo']


class EditarEquipoSerializer(serializers.ModelSerializer):
    """
    Serializador para editar equipo
    Valida:
    1. Unicidad de nombre dentro del proyecto.
    2. Que el nuevo cupo no sea menor al número de miembros activos actuales.
    """
    class Meta:
        model = Equipo
        fields = ['nombre', 'descripcion', 'cupo_maximo']

    def validate(self, data):
        equipo = self.instance

        nombre = data.get('nombre', equipo.nombre)
        # Validar que el nombre sea único dentro del proyecto
        if Equipo.objects.filter(
            nombre=nombre,
            proyecto=equipo.proyecto
        ).exclude(pk=equipo.pk).exists():
            raise serializers.ValidationError(
                {"nombre": "Ya existe un equipo con ese nombre en el proyecto."}
            )

        nuevo_cupo = data.get('cupo_maximo', equipo.cupo_maximo)
        # Contar solo miembros activos; los retirados no afectan límite de cupo
        miembros_activos = MiembroEquipo.objects.filter(
            equipo=equipo,
            estado='activo'
        ).count()
        # Validar que el cupo no sea menor a los miembros actuales
        if nuevo_cupo < miembros_activos:
            raise serializers.ValidationError(
                {"cupo_maximo": f"El cupo no puede ser menor al número de miembros activos ({miembros_activos})."}
            )

        return data


class EstudianteDisponibleSerializer(serializers.Serializer):
    id       = serializers.IntegerField()
    nombre   = serializers.CharField()
    apellido = serializers.CharField()
    correo   = serializers.EmailField()
    iniciales = serializers.SerializerMethodField()

    def get_iniciales(self, obj):
        n = obj.nombre[:1].upper()   if obj.nombre   else ''
        a = obj.apellido[:1].upper() if obj.apellido else ''
        return n + a


ROL_INTERNO_CHOICES = [
    ('lider', 'Líder'),
    ('desarrollador', 'Desarrollador'),
    ('disenador', 'Diseñador'),
    ('tester', 'Tester'),
    ('analista', 'Analista'),
]


# Serializer para actualizar el rol interno y responsabilidades de un miembro
# Valida que solo exista un Líder por equipo (validación de líder único)
# Usado por ActualizarRolView para PATCH sobre la membresía
class ActualizarRolSerializer(serializers.ModelSerializer):
    rol_interno = serializers.ChoiceField(choices=ROL_INTERNO_CHOICES)
    
    class Meta:
        model = MiembroEquipo
        fields = ['rol_interno', 'descripcion_responsabilidades']

    def validate(self, data):
        rol = data.get('rol_interno', '')
        if rol == 'lider':
            lider_existente = MiembroEquipo.objects.filter(
                equipo=self.instance.equipo,
                rol_interno='lider',
                estado='activo',
            ).exclude(pk=self.instance.pk)
            if lider_existente.exists():
                raise serializers.ValidationError(
                    "El equipo ya tiene un Líder asignado."
                )
        return data
