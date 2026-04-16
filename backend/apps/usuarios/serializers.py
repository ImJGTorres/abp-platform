from rest_framework import serializers
from apps.usuarios.models import Usuario
from django.contrib.auth.hashers import make_password 

class UsuarioSerializer(serializers.ModelSerializer):

    contrasena = serializers.CharField(
        write_only=True,   # nunca se devuelve en la respuesta
        min_length=8,
        error_messages={
            'min_length': 'La contraseña debe tener al menos 8 caracteres.'
        }
    )

    class Meta:
        model  = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo',
            'contrasena',  # ← se recibe pero nunca se devuelve (ST-06)
            'tipo_rol', 'estado', 'telefono', 'foto_perfil',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        extra_kwargs = {
            'fecha_creacion':      {'read_only': True},
            'fecha_actualizacion': {'read_only': True},
        }

    # Validar longitud mínima del nombre (ST-04)
    def validate_nombre(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return value

    # Validar longitud mínima del apellido (ST-04)
    def validate_apellido(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("El apellido debe tener al menos 2 caracteres.")
        return value

    # Validar que el rol sea uno de los permitidos (ST-04)
    def validate_tipo_rol(self, value):
        roles_validos = [r[0] for r in Usuario.TipoRol.choices]
        if value not in roles_validos:
            raise serializers.ValidationError(
                f"Rol inválido. Opciones válidas: {roles_validos}"
            )
        return value

    # El correo ya es validado automáticamente por EmailField,
    # pero agregamos unicidad explícita con mensaje descriptivo (ST-05)
    def validate_correo(self, value):
        qs = Usuario.objects.filter(correo=value)
        if self.instance:  # si es una actualización, excluimos el usuario actual
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo.")
        return value
    
    # ← NUEVO: al crear el usuario, hashea la contraseña antes de guardar (ST-06)
    def create(self, validated_data):
        contrasena = validated_data.pop('contrasena')
        validated_data['contrasena_hash'] = make_password(contrasena)
        return super().create(validated_data)


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'telefono', 'foto_perfil']
        extra_kwargs = {
            'telefono': {'required': False},
            'foto_perfil': {'required': False},
        }

    def validate_nombre(self, value):
        if value and len(value) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return value

    def validate_apellido(self, value):
        if value and len(value) < 2:
            raise serializers.ValidationError("El apellido debe tener al menos 2 caracteres.")
        return value