from django.conf import settings

from rest_framework import serializers

from .models import ArchivoAdjunto, Entregable
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
        ]


class EntregableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entregable
        fields = ['titulo', 'descripcion', 'tipo']

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
    class Meta:
        model = ArchivoAdjunto
        fields = [
            'id', 'id_entregable', 'nombre_original', 'nombre_almacenado',
            'ruta', 'tipo_mime', 'tamaño_bytes', 'version', 'fecha_subida',
        ]
        read_only_fields = fields


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
