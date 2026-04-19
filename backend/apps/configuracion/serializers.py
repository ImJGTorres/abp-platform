import re

from rest_framework import serializers
# serializers: Módulo de Django REST Framework para convertir modelos a JSON y viceversa

from .models import ParametroSistema, PeriodoAcademico
# ParametroSistema: Modelo de parámetros de configuración del sistema
# PeriodoAcademico: Modelo de períodos académicos


class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo PeriodoAcademico.
    
    Convierte objetos PeriodoAcademico a formato JSON para la API REST.
    El campo 'usuario_creo' se asigna automáticamente desde request.user.
    El campo 'total_cursos' es un campo calculado con el conteo de cursos asociados.
    """

    total_cursos = serializers.IntegerField(read_only=True)

    class Meta:
        model = PeriodoAcademico
        fields = [
            'id',
            'nombre',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'fecha_creacion',
            'usuario_creo',
            'total_cursos',
        ]
        read_only_fields = ['fecha_creacion', 'usuario_creo', 'total_cursos']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin = attrs.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )

        return attrs

    def validate_nombre(self, value):
        patron = re.compile(r'^\d{4}-[1-2]$')
        if not patron.match(value):
            raise serializers.ValidationError(
                {'nombre': 'El formato debe ser YYYY-N (ej: 2026-1 o 2026-2).'}
            )
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['usuario_creo'] = request.user
        return super().create(validated_data)


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
