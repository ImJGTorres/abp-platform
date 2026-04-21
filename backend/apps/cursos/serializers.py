from rest_framework import serializers

from .models import Curso, Proyecto


class ProyectoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Proyecto
        fields = [
            'id',
            'id_curso',
            'nombre',
            'descripcion',
            'estado',
            'fecha_inicio',
            'fecha_fin_estimada',
            'fecha_creacion',
        ]
        read_only_fields = ['fecha_creacion']

    def validate(self, attrs):
        attrs = super().validate(attrs)

        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin_estimada = attrs.get('fecha_fin_estimada')
        if fecha_inicio and fecha_fin_estimada and fecha_fin_estimada < fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin_estimada': 'La fecha fin estimada no puede ser anterior a la fecha de inicio.'}
            )

        return attrs

    def validate_id_curso(self, curso):
        request = self.context.get('request')
        if request is None:
            return curso

        usuario = getattr(request, 'user', None)
        if usuario is None or not usuario.is_authenticated:
            raise serializers.ValidationError('Se requiere autenticación.')

        if curso.id_docente_id != usuario.pk:
            raise serializers.ValidationError(
                'Solo el docente propietario del curso puede crear un proyecto en él.'
            )

        # Un curso solo puede tener un proyecto (OneToOne); verificar en creación
        if self.instance is None and hasattr(curso, 'proyecto'):
            raise serializers.ValidationError(
                'Este curso ya tiene un proyecto asignado.'
            )

        return curso