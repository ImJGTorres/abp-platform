from rest_framework import serializers

from apps.usuarios.models import UsuarioRol
from .models import Permiso, Rol, RolPermiso

# Serializer para CRUD de Permisos (modelo Permiso)
# Se usa en: GET/POST/PUT/PATCH /api/roles/permisos/
class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ['id', 'codigo', 'modulo', 'descripcion']

    # Validación: el código del permiso debe ser único en la BD
    # Ejemplo: "usuarios.ver" no puede repetirse
    # Si es update (self.instance existe), excluye el registro actual de la comparación
    def validate_codigo(self, value):
        qs = Permiso.objects.filter(codigo__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)  # Excluye el mismo registro en update
        if qs.exists():
            raise serializers.ValidationError('Ya existe un permiso con este código.')
        return value

# Serializer principal para operaciones CRUD de Rol
# - LECTURA (GET): devuelve el rol con sus permisos anidados
# - ESCRITURA (POST/PUT/PATCH): recibe permiso_ids para asignar permisos

# BE-03: Este serializer se usa en POST /api/roles/ para crear nuevos roles
class RolSerializer(serializers.ModelSerializer):
    # LECTURA: permisos - Devuelve la lista completa de permisos del rol
    # Este campo SOLO existe para lectura (no se envía en POST/PUT)
    # Se usa SerializerMethodField porque es un campo calculado (no es campo directo del modelo)
    permisos = serializers.SerializerMethodField()

    # LECTURA: total_usuarios - Cantidad de usuarios asignados a este rol (BE-02)
    total_usuarios = serializers.SerializerMethodField()

    # ESCRITURA: permiso_ids - Lista de IDs de permisos a asignar
    # Este campo SOLO existe para escritura (write_only=True)
    # En el JSON de entrada el cliente envía: "permiso_ids": [1, 2, 3]
    # El serializer convierte esos IDs a objetos Permiso usando el queryset
    permiso_ids = serializers.PrimaryKeyRelatedField(
        many=True,                    # Es una lista, no un solo valor
        queryset=Permiso.objects.all(),  # Busca permisos en la BD por ID
        write_only=True,              # Solo entrada, no se devuelve en respuesta
        required=False,               # Opcional: se puede omitir
    )

    class Meta:
        model = Rol
        # Campos del modelo Rol que se leen/escriben
        # Son los campos que se devuelven al hacer GET, y los que se aceptan en POST/PUT
        fields = ['id', 'nombre', 'descripcion', 'estado', 'fecha_creacion', 'total_usuarios', 'permisos', 'permiso_ids']
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},  # Se genera automáticamente, no envíar
        }

    # get_permisos(): permisos del rol para la respuesta
    # Se ejecuta al serializar (convertir a JSON) para devolver los permisos del rol
    # Busca en la tabla intermedia RolPermiso donde rol_id = obj.id
    def get_permisos(self, obj):
        # Busca todos los permisos relacionados a este rol
        permisos = Permiso.objects.filter(rolpermiso__rol=obj)
        # Convierte cada Permiso a JSON usando PermisoSerializer
        return PermisoSerializer(permisos, many=True).data

    # get_total_usuarios(): cantidad de usuarios asignados al rol (BE-02)
    # Cuenta los registros en UsuarioRol donde rol = este rol
    def get_total_usuarios(self, obj):
        return UsuarioRol.objects.filter(rol=obj).count()

    # validate_nombre(): Validar que el nombre del rol sea único
    # Se ejecuta automáticamente al recibir datos del cliente
    # Busca en la BD si ya existe un rol con ese nombre (case-insensitive)
    # Si es update (PUT/PATCH), excluye el registro actual para no dar error
    def validate_nombre(self, value):
        qs = Rol.objects.filter(nombre__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)  # En update, ignora el mismo registro
        if qs.exists():
            raise serializers.ValidationError('Ya existe un rol con este nombre.')
        return value

    # create(): Crear nuevo rol + asignar permisos
    # Se ejecuta cuando el método HTTP es POST (crear nuevo registro)
    # 1. Extrae permiso_ids de los datos validados
    # 2. Crea el Rol con los demás datos (nombre, descripcion)
    # 3. Crea un registro RolPermiso por cada permiso_id
    def create(self, validated_data):
        # Extrae la lista de permisos (se remueve de validated_data)
        permiso_list = validated_data.pop('permiso_ids', [])
        # Crea el rol en la BD
        rol = Rol.objects.create(**validated_data)
        # Por cada permiso en la lista, crea la relación en RolPermiso
        for permiso in permiso_list:
            RolPermiso.objects.create(rol=rol, permiso=permiso)
        return rol

    # update(): Actualizar rol + reemplazar permisos
    # Se ejecuta cuando el método HTTP es PUT/PATCH (actualizar registro)
    # 1. Actualiza los campos simples del rol (nombre, descripcion)
    # 2. Si vino permiso_ids: reemplaza TODOS los permisos actuales
    #    - Elimina todas las relaciones RolPermiso actuales
    #    - Crea nuevas relaciones con los permisos nuevos
    def update(self, instance, validated_data):
        # Extrae la lista de permisos (si vino en el request)
        permiso_list = validated_data.pop('permiso_ids', None)
        # Actualiza los campos simples del rol
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Si el cliente envió permiso_ids, reemplazar todos los permisos
        if permiso_list is not None:
            # Elimina TODAS las relaciones actuales (borra todo)
            RolPermiso.objects.filter(rol=instance).delete()
            # Crea las nuevas relaciones
            for permiso in permiso_list:
                RolPermiso.objects.create(rol=instance, permiso=permiso)
        return instance

# Serializer para la tabla intermedia RolPermiso (relación muchos a muchos)
# Se usa en: GET/POST/DELETE /api/roles/rol-permiso/
# Cada registro representa: "el rol X tiene el permiso Y"
class RolPermisoSerializer(serializers.ModelSerializer):
    # Campos calculados (solo lectura): nombre del rol y código del permiso
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    permiso_codigo = serializers.CharField(source='permiso.codigo', read_only=True)
    permiso_modulo = serializers.CharField(source='permiso.modulo', read_only=True)

    class Meta:
        model = RolPermiso
        # Campos que se devuelven: id, rol_id, permiso_id, y los nombres calculados
        fields = ['id', 'rol', 'permiso', 'rol_nombre', 'permiso_codigo', 'permiso_modulo']

    # Validación: impide asignar el mismo permiso dos veces al mismo rol
    def validate(self, data):
        qs = RolPermiso.objects.filter(rol=data['rol'], permiso=data['permiso'])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Este permiso ya está asignado al rol.')
        return data