from rest_framework import serializers

from .models import ParametroSistema


class ParametroSistemaSerializer(serializers.ModelSerializer):
    valor_casteado = serializers.SerializerMethodField()

    class Meta:
        model  = ParametroSistema
        fields = [
            'id',
            'clave',
            'valor',
            'valor_casteado',
            'descripcion',
            'categoria',
            'tipo_dato',
            'fecha_actualizacion',
            'usuario_modifico',
        ]
        read_only_fields = ['fecha_actualizacion']

    def get_valor_casteado(self, obj):
        return obj.get_valor_casteado()

    def validate(self, attrs):
        """
        Ejecuta clean() del modelo para reutilizar la misma lógica
        de validación de tipo_dato + valor sin duplicarla.
        """
        tipo  = attrs.get('tipo_dato', getattr(self.instance, 'tipo_dato', None))
        valor = attrs.get('valor',     getattr(self.instance, 'valor', None))

        instancia_temporal = ParametroSistema(
            tipo_dato=tipo,
            valor=valor or '',
        )
        instancia_temporal.clean()  # lanza ValidationError → DRF lo convierte a 400
        return attrs
