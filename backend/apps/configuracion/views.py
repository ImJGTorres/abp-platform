from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction, models

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento

from .cache import get_parametros_cacheados, set_parametros_cacheados, invalidar_cache_parametros
from .models import ParametroSistema, PeriodoAcademico
from .permissions import EsAdministrador, IsAdminOrDocente
from .serializers import ParametroSistemaSerializer, PeriodoAcademicoSerializer
from apps.cursos.models import Curso


class ConfiguracionView(APIView):
    """Vista para gestionar los parámetros de configuración del sistema.

    Endpoints:
        GET  /api/configuracion/         — Lista parámetros agrupados por categoría.
        PATCH /api/configuracion/<clave>/ — Actualiza el valor de un parámetro.

    Acceso restringido a administradores. GET consulta caché (TTL 15 min);
    PATCH invalida el caché tras una actualización exitosa.

    Ver también: api-contract.md § Configuración.
    """

    permission_classes = [EsAdministrador]

    def get(self, request):
        """Lista todos los parámetros agrupados por categoría.

        Returns:
            Response: Diccionario JSON con parámetros agrupados por categoría.
        """
        cached_data = get_parametros_cacheados()

        if cached_data is not None:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='configuracion',
                descripcion='Consulta de parámetros del sistema (desde caché)',
            )
            return Response(cached_data)

        parametros = ParametroSistema.objects.all()
        serializer = ParametroSistemaSerializer(parametros, many=True)

        agrupados = defaultdict(list)
        for item in serializer.data:
            agrupados[item['categoria']].append({
                'clave':               item['clave'],
                'valor':               item['valor'],
                'valor_casteado':      item['valor_casteado'],
                'descripcion':         item['descripcion'],
                'tipo_dato':           item['tipo_dato'],
                'fecha_actualizacion': item['fecha_actualizacion'],
            })

        result = dict(agrupados)
        set_parametros_cacheados(result)

        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='configuracion',
            descripcion='Consulta de parámetros del sistema',
        )

        return Response(result)

    def patch(self, request, clave):
        """Actualiza el valor de un parámetro del sistema.

        Args:
            request: Solicitud HTTP con body {'valor': str, 'rango': {'min': int, 'max': int}}.
            clave: Clave del parámetro a actualizar.

        Returns:
            Response: Datos del parámetro actualizado (200), o error 400/404.
        """
        try:
            parametro = ParametroSistema.objects.get(clave=clave)
        except ParametroSistema.DoesNotExist:
            return Response(
                {'detail': f'Parámetro "{clave}" no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        nuevo_valor = request.data.get('valor')
        if nuevo_valor is None:
            return Response(
                {'detail': 'El campo "valor" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rango = request.data.get('rango')
        if parametro.tipo_dato == ParametroSistema.TipoDato.INTEGER and rango:
            try:
                valor_int = int(nuevo_valor)
            except ValueError:
                return Response(
                    {'detail': f'Valor debe ser entero, recibido: "{nuevo_valor}"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'min' in rango and valor_int < rango['min']:
                return Response(
                    {'detail': f'Valor mínimo permitido: {rango["min"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'max' in rango and valor_int > rango['max']:
                return Response(
                    {'detail': f'Valor máximo permitido: {rango["max"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        valor_anterior = parametro.valor
        parametro.valor = str(nuevo_valor)
        parametro.usuario_modifico = request.user

        try:
            parametro.full_clean()
            parametro.save()
            invalidar_cache_parametros()
            if valor_anterior != parametro.valor:
                registrar_evento(
                    request,
                    accion=BitacoraSistema.Accion.UPDATE,
                    modulo='configuracion',
                    descripcion=f"Parámetro '{parametro.clave}' actualizado: '{valor_anterior}' → '{parametro.valor}'"
                )
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

        serializer = ParametroSistemaSerializer(parametro)
        return Response(serializer.data)


class PeriodoAcademicoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar períodos académicos.

    Endpoints:
        GET    /api/periodos/      — Lista períodos ordenados por fecha_inicio desc.
        POST   /api/periodos/      — Crea un período (admin).
        PUT    /api/periodos/<id>/ — Reemplaza un período (admin).
        PATCH  /api/periodos/<id>/ — Actualiza parcialmente (admin).
        DELETE /api/periodos/<id>/ — Elimina si no tiene cursos (admin).

    Ver también: api-contract.md § Períodos Académicos.
    """

    serializer_class = PeriodoAcademicoSerializer

    def get_queryset(self):
        return PeriodoAcademico.objects.annotate(
            total_cursos=models.Count('curso')
        ).order_by('-fecha_inicio')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdministrador()]
        return [IsAdminOrDocente()]

    def perform_create(self, serializer):
        serializer.save(usuario_creo=self.request.user)

    def _has_active_projects(self, periodo):
        from apps.cursos.models import Proyecto
        return Proyecto.objects.filter(
            id_curso__id_periodo_academico=periodo,
            estado=Proyecto.Estado.EN_EJECUCION,
        ).exists()

    def _get_active_projects_count(self, periodo):
        from apps.cursos.models import Proyecto
        return Proyecto.objects.filter(
            id_curso__id_periodo_academico=periodo,
            estado=Proyecto.Estado.EN_EJECUCION,
        ).count()

    def create(self, request, *args, **kwargs):
        """Crea un período; si el estado es activo, inactiva los períodos actuales."""
        estado = request.data.get('estado')

        if estado == PeriodoAcademico.Estado.ACTIVO:
            with transaction.atomic():
                PeriodoAcademico.objects.filter(
                    estado=PeriodoAcademico.Estado.ACTIVO
                ).update(estado=PeriodoAcademico.Estado.INACTIVO)

                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)

                try:
                    registrar_evento(
                        request,
                        accion=BitacoraSistema.Accion.CREATE,
                        modulo='periodos_academicos',
                        descripcion=f"Período académico creado: {serializer.instance.nombre}"
                    )
                except Exception:
                    pass

                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
        else:
            return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Actualiza un período. Bloquea cambio de fechas si hay proyectos activos.

        Args:
            request: Solicitud con datos del período. Acepta force_update=true para
                forzar el cambio de fechas aun con proyectos activos.
        """
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        nuevo_estado = serializer.validated_data.get('estado')
        nueva_fecha_inicio = serializer.validated_data.get('fecha_inicio')
        nueva_fecha_fin = serializer.validated_data.get('fecha_fin')
        force_update = request.data.get('force_update', False)

        fecha_cambio = (
            (nueva_fecha_inicio and nueva_fecha_inicio != instance.fecha_inicio) or
            (nueva_fecha_fin and nueva_fecha_fin != instance.fecha_fin)
        )

        if fecha_cambio and not force_update:
            proyectos_activos = self._get_active_projects_count(instance)
            if proyectos_activos > 0:
                return Response(
                    {'error': 'No se pueden modificar las fechas', 'proyectos_activos': proyectos_activos},
                    status=status.HTTP_409_CONFLICT
                )

        if nuevo_estado == PeriodoAcademico.Estado.ACTIVO and instance.estado != PeriodoAcademico.Estado.ACTIVO:
            with transaction.atomic():
                PeriodoAcademico.objects.filter(
                    estado=PeriodoAcademico.Estado.ACTIVO
                ).exclude(pk=instance.pk).update(estado=PeriodoAcademico.Estado.INACTIVO)

                self.perform_update(serializer)

                try:
                    registrar_evento(
                        request,
                        accion=BitacoraSistema.Accion.UPDATE,
                        modulo='periodos_academicos',
                        descripcion=f"Período académico actualizado: {serializer.instance.nombre}"
                    )
                except Exception:
                    pass

                return Response(serializer.data)
        else:
            self.perform_update(serializer)

            try:
                registrar_evento(
                    request,
                    accion=BitacoraSistema.Accion.UPDATE,
                    modulo='periodos_academicos',
                    descripcion=f"Período académico actualizado: {serializer.instance.nombre}"
                )
            except Exception:
                pass

            return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Elimina un período si no tiene cursos asociados.

        Returns:
            Response: 204 si se eliminó, 409 si hay cursos asociados.
        """
        instance = self.get_object()

        cursos_count = Curso.objects.filter(id_periodo_academico=instance).count()
        if cursos_count > 0:
            return Response(
                {'error': 'No se puede eliminar el periodo', 'cursos_afectados': cursos_count},
                status=status.HTTP_409_CONFLICT
            )

        nombre = instance.nombre
        self.perform_destroy(instance)

        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.DELETE,
                modulo='periodos_academicos',
                descripcion=f"Período académico eliminado: {nombre}"
            )
        except Exception:
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)
