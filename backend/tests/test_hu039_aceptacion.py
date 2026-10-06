"""
HU-039 — SCRUM-525: Prueba de aceptación.

Verifica que un anuncio publicado aparece de inmediato en el muro para todos
los roles y que se dispara la notificación por correo (en este sprint solo
se encola en cola_correo; el envío real es HU-043, Sprint 6).

Nota de alcance: el paso de la tarjeta "verifica que el estudiante no ve el
formulario de publicación" depende del frontend del muro de anuncios
(SCRUM-523, de Ovallos), que todavía no existe en el repositorio al momento
de esta prueba — no hay ningún componente de anuncios bajo frontend/src
(SCRUM-522, el mockup, sigue "En curso" según la guía del sprint). Por eso
este archivo solo cubre la parte verificable hoy (backend: API + cola_correo).
Ver docs/seguimiento_emerson_sprint5.md para el pendiente de verificación
visual una vez SCRUM-523 esté en develop.
"""
import pytest
from rest_framework.test import APIClient

from apps.alertas.models import ColaCorreo
from apps.anuncios.models import Anuncio
from apps.configuracion.models import ParametroSistema
from apps.usuarios.models import Usuario
from tests.factories import CursoFactory, EquipoFactory, MiembroEquipoFactory, ProyectoFactory, UsuarioFactory

ANUNCIO = {'titulo': 'Entrega adelantada', 'mensaje': 'La fase 2 se adelanta al lunes.'}


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


@pytest.mark.django_db
class TestAceptacionMuroDeAnuncios:
    """
    Escenario: el docente publica un anuncio en el muro del proyecto; el
    estudiante, el líder de equipo y el director lo ven de inmediato como
    primero en el muro, y queda un correo encolado por cada integrante.
    """

    def test_anuncio_publicado_aparece_primero_para_todos_los_roles_y_encola_correos(self):
        curso = CursoFactory()
        proyecto = ProyectoFactory(id_curso=curso)
        equipo = EquipoFactory(proyecto=proyecto)
        estudiante = UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)
        lider = UsuarioFactory(tipo_rol=Usuario.TipoRol.LIDER_EQUIPO)
        MiembroEquipoFactory(equipo=equipo, usuario=estudiante, rol_interno='desarrollador', estado='activo')
        MiembroEquipoFactory(equipo=equipo, usuario=lider, rol_interno='lider', estado='activo')
        director = UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR)

        url_muro = f'/api/proyectos/{proyecto.id}/anuncios/'
        # Anuncio anterior, para comprobar que el nuevo queda primero en el muro.
        Anuncio.objects.create(id_proyecto=proyecto, id_autor=curso.id_docente,
                               titulo='Anuncio viejo', mensaje='x')

        # 1. Publica como docente.
        r = _cliente(curso.id_docente).post(url_muro, ANUNCIO, format='json')
        assert r.status_code == 201

        # 2. Estudiante, líder y director lo ven de inmediato, primero en el muro.
        for usuario in (estudiante, lider, director):
            r = _cliente(usuario).get(url_muro)
            assert r.status_code == 200
            assert r.data[0]['titulo'] == ANUNCIO['titulo']

        # 3. Estudiante y líder no pueden publicar (RN-001) — el backend lo bloquea
        #    aunque la UI ya lo oculte (ver nota de alcance arriba).
        for usuario in (estudiante, lider):
            r = _cliente(usuario).post(url_muro, ANUNCIO, format='json')
            assert r.status_code == 403

        # 4. Correo: una fila en cola_correo por integrante del equipo (sin el autor).
        correos = ColaCorreo.objects.filter(plantilla='anuncio')
        assert sorted(correos.values_list('id_usuario_destino_id', flat=True)) == \
            sorted([estudiante.id, lider.id])
        contexto = correos.first().contexto
        assert contexto['titulo'] == ANUNCIO['titulo']
        assert contexto['proyecto_id'] == proyecto.id

    def test_anuncio_visible_desde_shell_en_cola_correo_por_integrante(self):
        """
        'Verifica en /django-admin/ o shell una fila anuncio en cola_correo por
        integrante' (SCRUM-525). Anuncio está registrado en /django-admin/
        (apps/anuncios/admin.py); ColaCorreo no tiene admin.py en apps/alertas,
        así que aquí se verifica por shell/ORM, la alternativa que la propia
        tarjeta permite.
        """
        from django.contrib import admin
        assert admin.site.is_registered(Anuncio)

        curso = CursoFactory()
        proyecto = ProyectoFactory(id_curso=curso)
        equipo = EquipoFactory(proyecto=proyecto)
        integrantes = [UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE) for _ in range(3)]
        for u in integrantes:
            MiembroEquipoFactory(equipo=equipo, usuario=u, estado='activo')

        r = _cliente(curso.id_docente).post(f'/api/proyectos/{proyecto.id}/anuncios/', ANUNCIO, format='json')
        assert r.status_code == 201

        filas = ColaCorreo.objects.filter(plantilla='anuncio', estado='pendiente')
        assert filas.count() == len(integrantes)
        assert sorted(filas.values_list('id_usuario_destino_id', flat=True)) == sorted(u.id for u in integrantes)
