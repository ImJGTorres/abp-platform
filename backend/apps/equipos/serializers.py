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


class EquipoCreateSerializer(serializers.ModelSerializer):
    capacidad_maxima = serializers.IntegerField(required=True)

    class Meta:
        model = Equipo
        fields = ['nombre', 'capacidad_maxima']

    def validate_capacidad_maxima(self, value):
        try:
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

    def create(self, validated_data):
        capacidad = validated_data.pop('capacidad_maxima')
        proyecto = self.context['proyecto']
        return Equipo.objects.create(proyecto=proyecto, nombre=validated_data['nombre'], cupo_maximo=capacidad)


class EquipoUpdateSerializer(serializers.ModelSerializer):
    capacidad_maxima = serializers.IntegerField(required=False)

    class Meta:
        model = Equipo
        fields = ['nombre', 'capacidad_maxima']

    def validate_capacidad_maxima(self, value):
        if value is not None:
            try:
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

    class Meta:
        model = Equipo
        fields = ['id', 'nombre', 'capacidad_maxima', 'numero_miembros']

    def get_numero_miembros(self, obj):
        return obj.miembros.filter(estado='activo').count()


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
