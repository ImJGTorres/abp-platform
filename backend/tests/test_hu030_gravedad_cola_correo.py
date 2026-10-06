"""
HU-030 — Gravedad de alertas y cola de correos (solo encolado; el envío es HU-043).
"""
from unittest.mock import patch, MagicMock

import pytest
from django.db import IntegrityError

from apps.alertas.models import Alerta
from apps.alertas.serializers import AlertaSerializer


class TestEncolarCorreo:

    @patch('apps.alertas.models.ColaCorreo.objects.create')
    def test_crea_fila_pendiente(self, mock_create):
        from apps.alertas.services import encolar_correo

        encolar_correo(5, 'Asunto', 'alerta', {'mensaje': 'x', 'proyecto_id': 1})

        mock_create.assert_called_once_with(
            id_usuario_destino_id=5,
            asunto='Asunto',
            plantilla='alerta',
            contexto={'mensaje': 'x', 'proyecto_id': 1},
        )

    def test_estado_por_defecto_es_pendiente(self):
        from apps.alertas.models import ColaCorreo
        correo = ColaCorreo(id_usuario_destino_id=1, asunto='a', plantilla='alerta')
        assert correo.estado == 'pendiente'
        assert correo.intentos == 0
        assert correo.fecha_envio is None


@patch('apps.alertas.services.transaction')
@patch('apps.alertas.services.encolar_correo')
@patch('apps.alertas.models.Alerta.objects.create')
class TestCrearAlertaGravedadYCola:

    @pytest.mark.parametrize('tipo, gravedad', [
        ('actividad_vencida', 'alta'),
        ('bajo_rendimiento', 'alta'),
        ('entregable_pendiente', 'media'),
        ('entregable_enviado', 'baja'),
        ('evaluacion_pendiente', 'baja'),
    ])
    def test_gravedad_por_tipo(self, mock_create, mock_encolar, mock_tx, tipo, gravedad):
        from apps.alertas.services import _crear_alerta

        _crear_alerta(tipo, usuario_id=1, mensaje='m')

        assert mock_create.call_args.kwargs['gravedad'] == gravedad

    def test_alerta_nueva_encola_correo(self, mock_create, mock_encolar, mock_tx):
        from apps.alertas.services import _crear_alerta
        mock_create.return_value = MagicMock(**{'get_tipo_display.return_value': 'Actividad vencida'})

        assert _crear_alerta('actividad_vencida', usuario_id=5, mensaje='Vencida',
                             proyecto_id=2, referencia_id=10) is True

        mock_encolar.assert_called_once_with(
            5, 'Nueva alerta: Actividad vencida', 'alerta',
            {'mensaje': 'Vencida', 'proyecto_id': 2},
        )

    def test_alerta_duplicada_no_encola(self, mock_create, mock_encolar, mock_tx):
        from apps.alertas.services import _crear_alerta
        mock_create.side_effect = IntegrityError

        assert _crear_alerta('actividad_vencida', usuario_id=5, mensaje='Vencida',
                             proyecto_id=2, referencia_id=10) is False

        mock_encolar.assert_not_called()


def test_serializer_expone_gravedad():
    alerta = Alerta(id=1, tipo='actividad_vencida', mensaje='m', gravedad='alta',
                    id_usuario_destino_id=1)
    data = AlertaSerializer(alerta).data
    assert data['gravedad'] == 'alta'
