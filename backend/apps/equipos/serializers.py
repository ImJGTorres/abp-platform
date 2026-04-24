from rest_framework import serializers

from apps.configuracion.models import ParametroSistema

from .models import Equipo, MiembroEquipo


# Serializador para crear y validar equipos.
# Valida que el cupo máximo no exceda el parámetro del sistema max_estudiantes_por_equipo.
class EquipoSerializer(serializers.ModelSerializer):
    # El proyecto se inyecta desde la vista, no se permite enviarlo en el request.
    proyecto = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Equipo
        fields = '__all__'

    # Valida que el cupo máximo no supere el límite configurado en el sistema.
    # Lee el parámetro max_estudiantes_por_equipo de la tabla de configuración.
    def validate_cupo_maximo(self, value):
        try:
            # Obtiene el parámetro de configuración que define el máximo de estudiantes por equipo.
            parametro = ParametroSistema.objects.get(clave='max_estudiantes_por_equipo')
            max_valor = int(parametro.valor)
        except ParametroSistema.DoesNotExist:
            raise serializers.ValidationError(
                "No se encontró el parámetro max_estudiantes_por_equipo en la configuración del sistema."
            )
        if value > max_valor:
            raise serializers.ValidationError(
                f"El cupo máximo no puede superar {max_valor} estudiantes por equipo."
            )
        return value


# Serializador para crear y validar membresías de usuarios en equipos.
# Valida que el usuario no pertenezca ya a otro equipo del mismo proyecto
# y que el equipo no haya excedido su cupo máximo.
# Requiere que la vista pase context={'equipo': equipo_instance} al instanciar este serializer.
class MiembroEquipoSerializer(serializers.ModelSerializer):
    # El equipo se inyecta desde la vista, no se permite enviarlo en el request.
    equipo = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MiembroEquipo
        fields = '__all__'

    def validate(self, data):
        # Obtiene el equipo del contexto (inyectado por la vista).
        equipo = self.context['equipo']
        usuario = data['usuario']
        proyecto = equipo.proyecto

        # Validación de negocio: un estudiante no puede pertenecer a dos equipos del mismo proyecto.
        # Busca membresías activas del usuario en equipos del mismo proyecto, excluyendo el equipo actual.
        ya_en_proyecto = MiembroEquipo.objects.filter(
            usuario=usuario,
            estado='activo',
            equipo__proyecto=proyecto,
        ).exclude(equipo=equipo).exists()

        if ya_en_proyecto:
            raise serializers.ValidationError(
                "El estudiante ya pertenece a otro equipo en este proyecto."
            )

        # Validación de negocio: el equipo no puede exceder su cupo máximo de integrantes.
        # Cuenta los miembros activos actuales del equipo.
        miembros_activos = MiembroEquipo.objects.filter(
            equipo=equipo,
            estado='activo',
        ).count()

        if miembros_activos >= equipo.cupo_maximo:
            raise serializers.ValidationError(
                f"El equipo ha alcanzado su cupo máximo de {equipo.cupo_maximo} integrantes."
            )

        return data


# ── Serializers de lectura (vistas de gestión y asignación) ──────────────────

class MiembroDetalleSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    iniciales       = serializers.SerializerMethodField()

    class Meta:
        model  = MiembroEquipo
        fields = ['id', 'usuario_id', 'nombre_completo', 'iniciales', 'rol_interno', 'estado']

    def get_nombre_completo(self, obj):
        return f"{obj.usuario.nombre} {obj.usuario.apellido}".strip()

    def get_iniciales(self, obj):
        n = obj.usuario.nombre[:1].upper()   if obj.usuario.nombre   else ''
        a = obj.usuario.apellido[:1].upper() if obj.usuario.apellido else ''
        return n + a


class EquipoDetalleSerializer(serializers.ModelSerializer):
    miembros             = serializers.SerializerMethodField()
    cantidad_miembros    = serializers.SerializerMethodField()
    lider                = serializers.SerializerMethodField()
    cantidad_entregables = serializers.SerializerMethodField()

    class Meta:
        model  = Equipo
        fields = [
            'id', 'nombre', 'descripcion', 'estado', 'cupo_maximo',
            'miembros', 'cantidad_miembros', 'lider', 'cantidad_entregables',
        ]

    def get_miembros(self, obj):
        activos = obj.miembros.filter(estado='activo').select_related('usuario')
        return MiembroDetalleSerializer(activos, many=True).data

    def get_cantidad_miembros(self, obj):
        return obj.miembros.filter(estado='activo').count()

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
