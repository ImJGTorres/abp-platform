# Para poblar la tabla con los parámetros iniciales ejecutar:
#   python manage.py loaddata parametros_iniciales

import re
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ParametroSistema(models.Model):

    class Categoria(models.TextChoices):
        INSTITUCIONAL = 'institucional', 'Institucional'
        SEGURIDAD     = 'seguridad',     'Seguridad'
        ARCHIVOS      = 'archivos',      'Archivos'
        SESIONES      = 'sesiones',      'Sesiones'
        GENERAL       = 'general',       'General'

    class TipoDato(models.TextChoices):
        STRING  = 'string',  'Texto'
        INTEGER = 'integer', 'Entero'
        BOOLEAN = 'boolean', 'Booleano'
        DATE    = 'date',    'Fecha'

    _BOOLEAN_TRUE  = {'true', '1', 'yes'}
    _BOOLEAN_FALSE = {'false', '0', 'no'}
    _DATE_RE       = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    clave               = models.CharField(max_length=100, unique=True)
    valor               = models.TextField()
    descripcion         = models.TextField(null=True, blank=True)
    categoria           = models.CharField(max_length=50, choices=Categoria.choices)
    tipo_dato           = models.CharField(max_length=20, choices=TipoDato.choices)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_modifico    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'parametro_sistema'
        ordering = ['categoria', 'clave']

    def clean(self):
        """Valida que `valor` sea compatible con `tipo_dato` antes de guardar."""
        v = (self.valor or '').strip()

        if self.tipo_dato == self.TipoDato.INTEGER:
            try:
                int(v)
            except ValueError:
                raise ValidationError(
                    {'valor': f'Se esperaba un entero, se recibió: "{v}"'}
                )

        elif self.tipo_dato == self.TipoDato.BOOLEAN:
            if v.lower() not in self._BOOLEAN_TRUE | self._BOOLEAN_FALSE:
                raise ValidationError(
                    {'valor': f'Se esperaba true/false/1/0/yes/no, se recibió: "{v}"'}
                )

        elif self.tipo_dato == self.TipoDato.DATE:
            if not self._DATE_RE.match(v):
                raise ValidationError(
                    {'valor': f'Se esperaba formato YYYY-MM-DD, se recibió: "{v}"'}
                )
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValidationError({'valor': f'Fecha inválida: "{v}"'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_valor_casteado(self):
        v = self.valor.strip()
        if self.tipo_dato == self.TipoDato.INTEGER:
            return int(v)
        if self.tipo_dato == self.TipoDato.BOOLEAN:
            return v.lower() in self._BOOLEAN_TRUE
        if self.tipo_dato == self.TipoDato.DATE:
            return date.fromisoformat(v)
        return self.valor  # STRING

    def __str__(self):
        return f'[{self.categoria}] {self.clave} = {self.valor}'
