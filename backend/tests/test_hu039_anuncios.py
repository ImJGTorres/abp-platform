"""
HU-039 — Muro de anuncios: modelo, serializador y publicación (SCRUM-517 / SCRUM-518).
"""
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from apps.anuncios.models import Anuncio
from apps.anuncios.serializers import AnuncioSerializer
from apps.usuarios.models import Usuario


def _ctx(tipo_rol):
    return {'request': SimpleNamespace(user=SimpleNamespace(tipo_rol=tipo_rol))}


class TestAnuncioModelo:

    def test_meta(self):
        assert Anuncio._meta.db_table == 'anuncio'
        assert Anuncio._meta.ordering == ['-fecha_publicacion']
        nombres = [c.name for c in Anuncio._meta.constraints]
        assert 'anuncio_curso_o_proyecto' in nombres


class TestAnuncioSerializerValidate:

    @pytest.mark.parametrize('rol', ['estudiante', 'lider_equipo', None])
    def test_rol_no_autorizado_falla(self, rol):
        s = AnuncioSerializer(context=_ctx(rol))
        with pytest.raises(Exception) as exc:
            s.validate({'id_curso': MagicMock(id=1), 'titulo': 't', 'mensaje': 'm'})
        assert 'Solo docentes' in str(exc.value)

    @pytest.mark.parametrize('rol', ['docente', 'director', 'administrador'])
    def test_rol_autorizado_pasa(self, rol):
        s = AnuncioSerializer(context=_ctx(rol))
        attrs = {'id_curso': MagicMock(id=1), 'titulo': 't', 'mensaje': 'm'}
        assert s.validate(attrs) is attrs

    def test_sin_curso_ni_proyecto_falla(self):
        s = AnuncioSerializer(context=_ctx('docente'))
        with pytest.raises(Exception) as exc:
            s.validate({'titulo': 't', 'mensaje': 'm'})
        assert 'curso o a un proyecto' in str(exc.value)

    def test_proyecto_de_otro_curso_falla(self):
        s = AnuncioSerializer(context=_ctx('docente'))
        with pytest.raises(Exception) as exc:
            s.validate({'id_curso': MagicMock(id=1), 'id_proyecto': MagicMock(id_curso_id=2),
                        'titulo': 't', 'mensaje': 'm'})
        assert 'no pertenece al curso' in str(exc.value)


def test_autor_se_serializa_como_objeto():
    autor = Usuario(id=7, nombre='Ana', apellido='Pérez')
    anuncio = Anuncio(id=1, id_curso_id=3, id_autor=autor, titulo='t', mensaje='m')
    assert AnuncioSerializer(anuncio).data['autor'] == {'id': 7, 'nombre': 'Ana', 'apellido': 'Pérez'}


@patch('apps.bitacora.utils.registrar_evento')
@patch('apps.alertas.services.encolar_correo')
@patch('apps.anuncios.services._destinatarios')
@patch('apps.anuncios.models.Anuncio.objects.create')
@patch('apps.anuncios.services.transaction')
class TestPublicarAnuncio:

    def test_guarda_encola_y_registra(self, mock_tx, mock_create, mock_dest, mock_encolar, mock_bitacora):
        from apps.anuncios.services import publicar_anuncio
        autor = SimpleNamespace(id=1, nombre='Doc', apellido='Ente')
        anuncio = MagicMock(id=10, titulo='Entrega', mensaje='Recuerden', id_curso_id=3, id_proyecto_id=None)
        mock_create.return_value = anuncio
        mock_dest.return_value = [20, 21, 22]
        request = MagicMock()

        resultado = publicar_anuncio(autor, {'id_curso': 'curso', 'titulo': 'Entrega', 'mensaje': 'Recuerden'}, request)

        assert resultado is anuncio
        mock_create.assert_called_once_with(id_autor=autor, id_curso='curso', titulo='Entrega', mensaje='Recuerden')
        assert mock_encolar.call_count == 3
        assert [c.args[0] for c in mock_encolar.call_args_list] == [20, 21, 22]
        assert all(c.args[1:3] == ('Nuevo anuncio: Entrega', 'anuncio') for c in mock_encolar.call_args_list)
        assert mock_encolar.call_args.args[3]['anuncio_id'] == 10
        args = mock_bitacora.call_args.args
        assert args[0] is request and args[1] == 'CREATE' and args[2] == 'anuncios'
        assert 'correos encolados=3' in args[3]

    def test_sin_destinatarios_no_encola(self, mock_tx, mock_create, mock_dest, mock_encolar, mock_bitacora):
        from apps.anuncios.services import publicar_anuncio
        mock_create.return_value = MagicMock(id=11, titulo='t', mensaje='m', id_curso_id=3, id_proyecto_id=None)
        mock_dest.return_value = []

        publicar_anuncio(SimpleNamespace(id=1, nombre='a', apellido='b'), {}, MagicMock())

        mock_encolar.assert_not_called()
        mock_bitacora.assert_called_once()
