from rest_framework import serializers

from .models import Entregable
from apps.equipos.models import MiembroEquipo


class EntregableSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(read_only=True)
    fecha_envio = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Entregable
        fields = [
            'id',
            'id_actividad',
            'id_equipo',
            'titulo',
            'descripcion',
            'tipo',
            'estado',
            'fecha_envio',
            'fecha_creacion',
        ]


class EntregableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entregable
        fields = ['titulo', 'descripcion', 'tipo']

    def validate(self, attrs):
        request = self.context['request']
        actividad = self.context['actividad']
        usuario = request.user

        proyecto = actividad.id_fase.id_proyecto

        es_miembro = MiembroEquipo.objects.filter(
            usuario=usuario,
            equipo__proyecto=proyecto,
            estado='activo',
        ).exists()

        if not es_miembro:
            raise serializers.ValidationError(
                'No perteneces a un equipo activo en este proyecto.'
            )

        return attrs
