from django.db.models import Count
from rest_framework import serializers

from apps.usuarios.models import Usuario
from .models import Permiso, Rol, RolPermiso


class RolListSerializer(serializers.ModelSerializer):
    total_usuarios = serializers.SerializerMethodField()

    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion', 'estado', 'total_usuarios']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        nombre = instance.nombre.replace('_', ' ').title()
        data['nombre'] = nombre
        return data

    def get_total_usuarios(self, obj):
        return self.context.get('usuarios_por_rol', {}).get(obj.id, 0)


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ['id', 'codigo', 'modulo', 'descripcion']

    def validate_codigo(self, value):
        qs = Permiso.objects.filter(codigo__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un permiso con este código.')
        return value


class RolSerializer(serializers.ModelSerializer):
    # Lectura: permisos anidados completos
    permisos = serializers.SerializerMethodField()

    # Escritura: lista de IDs de permisos a asignar (reemplaza los actuales)
    permiso_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permiso.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion', 'estado', 'fecha_creacion', 'permisos', 'permiso_ids']
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }

    def get_permisos(self, obj):
        permisos = Permiso.objects.filter(rolpermiso__rol=obj)
        return PermisoSerializer(permisos, many=True).data

    def validate_nombre(self, value):
        qs = Rol.objects.filter(nombre__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un rol con este nombre.')
        return value

    def create(self, validated_data):
        permiso_list = validated_data.pop('permiso_ids', [])
        rol = Rol.objects.create(**validated_data)
        for permiso in permiso_list:
            RolPermiso.objects.create(rol=rol, permiso=permiso)
        return rol

    def update(self, instance, validated_data):
        permiso_list = validated_data.pop('permiso_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if permiso_list is not None:
            # Reemplaza todos los permisos del rol de una sola vez
            RolPermiso.objects.filter(rol=instance).delete()
            for permiso in permiso_list:
                RolPermiso.objects.create(rol=instance, permiso=permiso)
        return instance


class RolPermisoSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    permiso_codigo = serializers.CharField(source='permiso.codigo', read_only=True)
    permiso_modulo = serializers.CharField(source='permiso.modulo', read_only=True)

    class Meta:
        model = RolPermiso
        fields = ['id', 'rol', 'permiso', 'rol_nombre', 'permiso_codigo', 'permiso_modulo']

    def validate(self, data):
        qs = RolPermiso.objects.filter(rol=data['rol'], permiso=data['permiso'])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Este permiso ya está asignado al rol.')
        return data