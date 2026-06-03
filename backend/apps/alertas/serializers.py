from rest_framework import serializers
from .models import Alerta


class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = [
            'id', 'tipo', 'mensaje', 'estado',
            'fecha_generacion', 'fecha_lectura',
            'id_proyecto_id', 'referencia_id',
        ]
        read_only_fields = fields
