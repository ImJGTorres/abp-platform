"""
HU-035 — Identidad institucional (SCRUM-606).
"""
from unittest.mock import patch, MagicMock

from apps.configuracion.identidad import obtener_identidad
from apps.configuracion.models import IdentidadInstitucional


def _parametros(valores):
    """Simula ParametroSistema.objects.filter(clave=...).values_list(...).first()."""
    def _filter(clave):
        qs = MagicMock()
        qs.values_list.return_value.first.return_value = valores.get(clave)
        return qs
    return _filter


@patch('apps.configuracion.models.ParametroSistema.objects.filter')
@patch('apps.configuracion.models.IdentidadInstitucional.objects.get_or_create')
class TestObtener:

    def test_sin_parametros_usa_constantes(self, mock_goc, mock_filter):
        mock_filter.side_effect = _parametros({})
        mock_goc.return_value = (MagicMock(), True)

        IdentidadInstitucional.obtener()

        assert mock_goc.call_args.kwargs['pk'] == 1
        assert mock_goc.call_args.kwargs['defaults'] == {
            'nombre_institucion': 'UFPS — Plataforma ABP',
            'programa_academico': 'Ingeniería de Sistemas',
        }

    def test_toma_valores_de_parametro_sistema(self, mock_goc, mock_filter):
        mock_filter.side_effect = _parametros({
            'nombre_institucion': 'Universidad Francisco de Paula Santander',
            'nombre_programa': 'Ingeniería Electrónica',
        })
        mock_goc.return_value = (MagicMock(), True)

        IdentidadInstitucional.obtener()

        assert mock_goc.call_args.kwargs['defaults'] == {
            'nombre_institucion': 'Universidad Francisco de Paula Santander',
            'programa_academico': 'Ingeniería Electrónica',
        }

    def test_parametro_vacio_usa_constante(self, mock_goc, mock_filter):
        mock_filter.side_effect = _parametros({'nombre_institucion': '  ', 'nombre_programa': ''})
        mock_goc.return_value = (MagicMock(), True)

        IdentidadInstitucional.obtener()

        defaults = mock_goc.call_args.kwargs['defaults']
        assert defaults['nombre_institucion'] == 'UFPS — Plataforma ABP'
        assert defaults['programa_academico'] == 'Ingeniería de Sistemas'


@patch('apps.configuracion.identidad.IdentidadInstitucional.obtener')
class TestObtenerIdentidad:

    def test_sin_logotipo(self, mock_obtener):
        mock_obtener.return_value = IdentidadInstitucional(
            pk=1, nombre_institucion='UFPS', programa_academico='Sistemas'
        )

        assert obtener_identidad() == {
            'nombre_institucion': 'UFPS',
            'programa_academico': 'Sistemas',
            'logotipo_path': None,
            'logotipo_url': None,
        }

    def test_con_logotipo_en_disco(self, mock_obtener, tmp_path, settings):
        settings.MEDIA_ROOT = str(tmp_path)
        (tmp_path / 'identidad').mkdir()
        (tmp_path / 'identidad' / 'logo.png').write_bytes(b'png')
        mock_obtener.return_value = IdentidadInstitucional(
            pk=1, nombre_institucion='UFPS', programa_academico='Sistemas',
            logotipo='identidad/logo.png',
        )

        datos = obtener_identidad()

        assert datos['logotipo_path'] == str(tmp_path / 'identidad' / 'logo.png')
        assert datos['logotipo_url'].endswith('/media/identidad/logo.png')

    def test_logotipo_inexistente_path_none(self, mock_obtener, tmp_path, settings):
        settings.MEDIA_ROOT = str(tmp_path)
        mock_obtener.return_value = IdentidadInstitucional(
            pk=1, nombre_institucion='UFPS', programa_academico='Sistemas',
            logotipo='identidad/no_existe.png',
        )

        datos = obtener_identidad()

        assert datos['logotipo_path'] is None
        assert datos['logotipo_url'].endswith('/media/identidad/no_existe.png')


def test_admin_solo_superusuario():
    """/django-admin/ necesita has_perm y has_module_perms en Usuario."""
    from apps.usuarios.models import Usuario
    assert Usuario(is_superuser=True).has_perm('configuracion.change_identidadinstitucional')
    assert Usuario(is_superuser=True).has_module_perms('configuracion')
    assert not Usuario(is_staff=True).has_perm('configuracion.change_identidadinstitucional')
    assert not Usuario(is_staff=True).has_module_perms('configuracion')
