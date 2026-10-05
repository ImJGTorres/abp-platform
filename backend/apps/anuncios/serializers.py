from rest_framework import serializers

from .models import Anuncio

ROLES_AUTOR = ('docente', 'director', 'administrador')


class AnuncioSerializer(serializers.ModelSerializer):
    autor = serializers.SerializerMethodField()

    class Meta:
        model = Anuncio
        fields = [
            'id', 'id_curso', 'id_proyecto', 'autor',
            'titulo', 'mensaje', 'fecha_publicacion', 'fecha_creacion',
        ]
        read_only_fields = ['id', 'autor', 'fecha_creacion']

    def get_autor(self, obj):
        autor = obj.id_autor
        return {'id': autor.id, 'nombre': autor.nombre, 'apellido': autor.apellido}

    def validate(self, attrs):
        request = self.context.get('request')
        tipo_rol = getattr(getattr(request, 'user', None), 'tipo_rol', None)
        if tipo_rol not in ROLES_AUTOR:
            raise serializers.ValidationError(
                'Solo docentes, directores o administradores pueden publicar anuncios.'
            )

        curso = attrs.get('id_curso', getattr(self.instance, 'id_curso', None))
        proyecto = attrs.get('id_proyecto', getattr(self.instance, 'id_proyecto', None))
        if not curso and not proyecto:
            raise serializers.ValidationError('El anuncio debe pertenecer a un curso o a un proyecto.')
        if curso and proyecto and proyecto.id_curso_id != curso.id:
            raise serializers.ValidationError({'id_proyecto': 'El proyecto no pertenece al curso indicado.'})
        return attrs
