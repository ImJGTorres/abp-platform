from rest_framework import serializers
# serializers: Módulo de Django REST Framework para convertir modelos a JSON y viceversa

from .models import ParametroSistema
# ParametroSistema: Modelo de parámetros de configuración del sistema


class ParametroSistemaSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo ParametroSistema.
    
    Convierte objetos ParametroSistema a formato JSON para la API REST.
    Expone campos como clave, valor, valor_casteado, descripcion, etc.
    
    El campo 'valor_casteado' es especialmente importante porque permite
    a los clientes obtener el valor ya convertido al tipo correcto (int, bool, date).
    """
    
    # valor_casteado: Campo de solo lectura que expone el valor convertido al tipo correcto
    # Se usa SerializerMethodField porque requiere ejecutar lógica personalizada (get_valor_casteado)
    # Este campo NO se puede modificar desde la API, solo se lee
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
        # fecha_actualizacion es de solo lectura porque se actualiza automáticamente
        read_only_fields = ['fecha_actualizacion']

    def get_valor_casteado(self, obj):
        """Convierte el valor al tipo correcto del parámetro.
        
        Args:
            obj: Instancia del modelo ParametroSistema
            
        Returns:
            El valor casteado según el tipo_dato:
            - int para tipo 'integer'
            - bool para tipo 'boolean'
            - date para tipo 'date'
            - str para tipo 'string'
        
        Ejemplo de respuesta API:
            "valor": "30"
            "valor_casteado": 30  # type: integer
        """
        return obj.get_valor_casteado()

    def validate(self, attrs):
        """
        Valida que el valor sea compatible con el tipo_dato.
        
        Este método reutiliza la lógica de validación del modelo (clean())
        en lugar de duplicarla. Esto asegura consistencia entre:
        - Validación desde el admin de Django
        - Validación desde la API REST
        - Validación desde el serializador
        
        Si la validación falla (ej: tipo integer con valor "abc"),
        DRF captura la ValidationError y retorna automáticamente
        un HTTP 400 Bad Request con el mensaje de error.
        """
        # Obtiene tipo_dato y valor de los datos enviados (o usa los existentes si es actualización)
        tipo  = attrs.get('tipo_dato', getattr(self.instance, 'tipo_dato', None))
        valor = attrs.get('valor',     getattr(self.instance, 'valor', None))

        # Crea una instancia temporal del modelo solo con los campos a validar
        # No se guarda en BD, solo se usa para ejecutar clean()
        instancia_temporal = ParametroSistema(
            tipo_dato=tipo,
            valor=valor or '',
        )
        
        # clean() valida el valor según el tipo_dato
        # Si falla, lanza ValidationError que DRF convierte a respuesta 400
        instancia_temporal.clean()
        
        return attrs
