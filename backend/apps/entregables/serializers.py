from django.conf import settings

from rest_framework import serializers

from .models import ArchivoAdjunto, Entregable, EntregableVersion, Notificacion
from apps.equipos.models import MiembroEquipo


class EntregableSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(read_only=True)
    fecha_envio = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Entregable
        fields = [
            'id',
            'id_actividad',
            'id_equipo',
            'titulo',
            'descripcion',
            'tipo',
            'estado',
            'fecha_envio',
            'fecha_creacion',
            'numero_version',
            'id_version_anterior',
        ]


class EntregableVersionDetalleSerializer(serializers.Serializer):
    numero_version = serializers.IntegerField()
    id_entregable = serializers.IntegerField(source='id_version_id')
    estado = serializers.SerializerMethodField()
    fecha_creacion = serializers.SerializerMethodField()
    fecha_envio = serializers.SerializerMethodField()
    motivo_revision = serializers.CharField()
    archivos = serializers.SerializerMethodField()
    retroalimentacion = serializers.SerializerMethodField()

    def get_estado(self, obj):
        return obj.id_version.estado

    def get_fecha_creacion(self, obj):
        return obj.id_version.fecha_creacion

    def get_fecha_envio(self, obj):
        return obj.id_version.fecha_envio

    def get_archivos(self, obj):
        archivos = obj.id_version.archivos.all()
        request = self.context.get('request')
        return ArchivoAdjuntoSerializer(archivos, many=True, context={'request': request}).data

    def get_retroalimentacion(self, obj):
        return getattr(obj.id_version, 'retroalimentacion', None)


class ValidarEntregableSerializer(serializers.Serializer):
    accion = serializers.ChoiceField(choices=['aprobar', 'rechazar'])
    retroalimentacion = serializers.CharField(required=False, allow_blank=True, default='')


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'tipo', 'titulo_entregable', 'retroalimentacion', 'id_entregable', 'leida', 'fecha_creacion']
        read_only_fields = fields


class EntregableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entregable
        fields = ['titulo', 'descripcion', 'tipo']
        extra_kwargs = {
            'descripcion': {'required': False, 'allow_blank': True, 'default': ''},
        }

    def validate(self, attrs):
        request = self.context['request']
        actividad = self.context['actividad']
        usuario = request.user

        proyecto = actividad.id_fase.id_proyecto

        es_miembro = MiembroEquipo.objects.filter(
            usuario=usuario,
            equipo__proyecto=proyecto,
            estado='activo',
        ).exists()

        if not es_miembro:
            raise serializers.ValidationError(
                'No perteneces a un equipo activo en este proyecto.'
            )

        return attrs


MIME_EXTENSION_MAP = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
}


class ArchivoAdjuntoSerializer(serializers.ModelSerializer):
    url_descarga = serializers.SerializerMethodField()

    class Meta:
        model = ArchivoAdjunto
        fields = [
            'id', 'id_entregable', 'nombre_original', 'nombre_almacenado',
            'ruta', 'tipo_mime', 'tamaño_bytes', 'version', 'fecha_subida',
            'url_descarga'
        ]
        read_only_fields = fields

    def get_url_descarga(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f"{settings.MEDIA_URL}{obj.ruta}")
        return f"{settings.MEDIA_URL}{obj.ruta}"


class EntregableValidacionSerializer(serializers.ModelSerializer):
    """Serializador de lectura para respuesta post-validación."""
    class Meta:
        model = Entregable
        fields = [
            'id', 'titulo', 'estado', 'retroalimentacion',
            'fecha_validacion', 'id_docente_validador', 'numero_version'
        ]
        read_only_fields = fields


class EntregablePendienteSerializer(serializers.ModelSerializer):
    """Serializador para listado de entregables pendientes del docente."""
    nombre_equipo = serializers.CharField(source='id_equipo.nombre', read_only=True)
    nombre_actividad = serializers.CharField(source='id_actividad.nombre', read_only=True)

    class Meta:
        model = Entregable
        fields = [
            'id', 'titulo', 'estado', 'fecha_envio',
            'numero_version', 'nombre_equipo', 'nombre_actividad'
        ]


class SubirArchivoSerializer(serializers.Serializer):
    archivo = serializers.FileField()

    def validate_archivo(self, archivo):
        try:
            from apps.configuracion.models import ParametroSistema
            param = ParametroSistema.objects.get(clave='formatos_archivo_permitidos')
            extensiones_permitidas = [e.strip().lower() for e in param.valor.split(',')]
        except Exception:
            extensiones_permitidas = ['pdf', 'docx', 'xlsx', 'png', 'jpg', 'jpeg']

        nombre = archivo.name
        ext = nombre.rsplit('.', 1)[-1].lower() if '.' in nombre else ''
        if ext not in extensiones_permitidas:
            raise serializers.ValidationError(
                f"Formato no permitido. Extensiones aceptadas: {', '.join(extensiones_permitidas)}"
            )

        max_size = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 10 * 1024 * 1024)
        if archivo.size > max_size:
            raise serializers.ValidationError(
                f"El archivo excede el tamaño máximo permitido ({max_size // (1024 * 1024)} MB)."
            )

        archivo._tipo_mime = MIME_EXTENSION_MAP.get(ext, archivo.content_type or 'application/octet-stream')
        return archivo
