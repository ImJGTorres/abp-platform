from rest_framework import serializers

from apps.configuracion.models import ParametroSistema

from .models import Equipo, MiembroEquipo


class EquipoSerializer(serializers.ModelSerializer):
    proyecto = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Equipo
        fields = '__all__'

    def validate_cupo_maximo(self, value):
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


# Requiere que la vista pase context={'equipo': equipo_instance} al instanciar este serializer.
class MiembroEquipoSerializer(serializers.ModelSerializer):
    equipo = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MiembroEquipo
        fields = '__all__'

    def validate(self, data):
        equipo = self.context['equipo']
        usuario = data['usuario']
        proyecto = equipo.proyecto

        ya_en_proyecto = MiembroEquipo.objects.filter(
            usuario=usuario,
            estado='activo',
            equipo__proyecto=proyecto,
        ).exclude(equipo=equipo).exists()

        if ya_en_proyecto:
            raise serializers.ValidationError(
                "El estudiante ya pertenece a otro equipo en este proyecto."
            )

        miembros_activos = MiembroEquipo.objects.filter(
            equipo=equipo,
            estado='activo',
        ).count()

        if miembros_activos >= equipo.cupo_maximo:
            raise serializers.ValidationError(
                f"El equipo ha alcanzado su cupo máximo de {equipo.cupo_maximo} integrantes."
            )

        return data
