from rest_framework import serializers
from apps.bitacora.models import BitacoraSistema


class BitacoraSerializer(serializers.ModelSerializer):
    # Campo personalizado para mostrar los datos completos del usuario en lugar de solo el ID
    id_usuario = serializers.SerializerMethodField()
    
    class Meta:
        model = BitacoraSistema
        fields = [
            'id',
            'id_usuario',
            'nombre_usuario',
            'accion',
            'modulo',
            'descripcion',
            'ip_origen',
            'fecha_hora',
        ]
    
    def get_id_usuario(self, obj):
        """Retorna un diccionario con los datos del usuario (id, correo, nombre completo)."""
        if obj.id_usuario is not None:
            return {
                'id': obj.id_usuario.id,
                'correo': obj.id_usuario.correo,
                'nombre': f'{obj.id_usuario.nombre} {obj.id_usuario.apellido}',
            }
        return None