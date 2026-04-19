from rest_framework import serializers
from apps.usuarios.models import Usuario

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
    
    # Crea el usuario hasheando la contraseña de forma segura (ST-06).
    # Antes se usaba make_password() y se guardaba en 'contrasena_hash' manualmente.
    # Ahora se usa set_password() que es el método oficial de AbstractBaseUser:
    # internamente también llama a make_password(), pero además marca al objeto
    # como "contraseña establecida", lo que permite usar check_password() en el login.
    def create(self, validated_data):
        # Extrae 'contrasena' del dict — no es un campo del modelo, solo se usa aquí
        contrasena = validated_data.pop('contrasena')
        # Construye la instancia con el resto de los campos (nombre, correo, etc.)
        usuario = Usuario(**validated_data)
        # Hashea la contraseña y la almacena en el campo 'password' de AbstractBaseUser
        usuario.set_password(contrasena)
        usuario.save()
        return usuario


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de perfil (PATCH).
    - Campos libres para cualquier usuario autenticado: nombre, apellido, telefono, foto_perfil.
    - Campos restringidos a administrador: correo, tipo_rol.
    La vista es responsable de pasar el contexto con el request para aplicar las restricciones.
    """

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'tipo_rol', 'telefono', 'foto_perfil']

    CAMPOS_ADMIN = {'correo', 'tipo_rol'}

    def validate(self, attrs):
        request = self.context.get('request')
        es_admin = (
            request is not None
            and request.user.is_authenticated
            and request.user.tipo_rol == Usuario.TipoRol.ADMINISTRADOR
        )
        campos_restringidos = set(attrs.keys()) & self.CAMPOS_ADMIN
        if campos_restringidos and not es_admin:
            raise serializers.ValidationError(
                {campo: "Solo un administrador puede modificar este campo."
                 for campo in campos_restringidos}
            )
        return attrs

    def validate_nombre(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return value

    def validate_apellido(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("El apellido debe tener al menos 2 caracteres.")
        return value

    def validate_tipo_rol(self, value):
        roles_validos = [r[0] for r in Usuario.TipoRol.choices]
        if value not in roles_validos:
            raise serializers.ValidationError(
                f"Rol inválido. Opciones válidas: {roles_validos}"
            )
        return value

    def validate_correo(self, value):
        qs = Usuario.objects.filter(correo=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo.")
        return value
