# Para poblar la tabla con los parámetros iniciales ejecutar:
#   python manage.py loaddata parametros_iniciales
# Este comando carga los datos iniciales desde un archivo fixture JSON/YAML

import math
import re
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PeriodoAcademico(models.Model):
    """
    Modelo que representa un período académico del sistema.
    Cada período tiene fecha de inicio, fecha fin y un estado.
    """

    class Estado(models.TextChoices):
        ACTIVO   = 'activo',   'Activo'
        INACTIVO = 'inactivo', 'Inactivo'
        CERRADO  = 'cerrado',  'Cerrado'

    nombre = models.CharField(max_length=50, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVO,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario_creo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'periodo_academico'
        constraints = [
            models.CheckConstraint(
                check=models.Q(fecha_fin__gt=models.F('fecha_inicio')),
                name='fecha_fin_posterior_fecha_inicio',
            )
        ]

    def clean(self):
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )

    def __str__(self):
        return self.nombre


class ParametroSistema(models.Model):
    """
    Modelo que representa un parámetro de configuración del sistema.
    Cada parámetro tiene una clave única, valor, categoría y tipo de dato.
    Se utiliza para almacenar configuraciones globales que pueden ser
    consultadas y modificadas dinámicamente sin reiniciar el servidor.
    """

    class Categoria(models.TextChoices):
        INSTITUCIONAL = 'institucional', 'Institucional'
        SEGURIDAD     = 'seguridad',     'Seguridad'
        ARCHIVOS      = 'archivos',      'Archivos'
        SESIONES      = 'sesiones',      'Sesiones'
        GENERAL       = 'general',       'General'
        RENDIMIENTO   = 'rendimiento',   'Rendimiento'  # usada por la migración 0004

    class TipoDato(models.TextChoices):
        STRING  = 'string',  'Texto'
        INTEGER = 'integer', 'Entero'
        BOOLEAN = 'boolean', 'Booleano'
        DATE    = 'date',    'Fecha'
        FLOAT   = 'float',   'Decimal'  # umbrales de nota (migraciones 0004 y 0007)

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
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'parametro_sistema'
        ordering = ['categoria', 'clave']

    def _castear_valor(self, v: str):
        """Convierte y valida una cadena según tipo_dato.

        Centraliza la lógica compartida entre clean() y get_valor_casteado().

        Reglas de validación por tipo:
            - INTEGER: debe ser un número entero no negativo (>= 0).
            - FLOAT:   debe ser un número decimal no negativo (>= 0), p. ej. 3.5.
            - BOOLEAN: debe ser uno de true/false/1/0/yes/no (insensible a mayúsculas).
            - DATE:    debe respetar el formato YYYY-MM-DD.
            - STRING:  se acepta cualquier valor de texto sin restricciones.

        Args:
            v: Valor en formato string (ya sin espacios).

        Returns:
            int | float | bool | date | str: Valor convertido al tipo Python correspondiente.

        Raises:
            ValueError: Si la conversión falla o el valor no cumple las restricciones
                        de rango o formato. El mensaje describe el motivo específico.
        """
        if self.tipo_dato == self.TipoDato.INTEGER:
            try:
                resultado = int(v)
            except (ValueError, TypeError):
                raise ValueError(
                    f'Se esperaba un número entero, se recibió: "{v}"'
                )
            if resultado < 0:
                raise ValueError(
                    f'El valor entero debe ser mayor o igual a 0, se recibió: {resultado}'
                )
            return resultado
        if self.tipo_dato == self.TipoDato.FLOAT:
            try:
                resultado = float(v)
            except (ValueError, TypeError):
                raise ValueError(
                    f'Se esperaba un número decimal (ej. 3.5), se recibió: "{v}"'
                )
            if not math.isfinite(resultado) or resultado < 0:
                raise ValueError(
                    f'El valor decimal debe ser un número mayor o igual a 0, se recibió: "{v}"'
                )
            return resultado
        if self.tipo_dato == self.TipoDato.BOOLEAN:
            valores_validos = self._BOOLEAN_TRUE | self._BOOLEAN_FALSE
            if v.lower() not in valores_validos:
                raise ValueError(
                    f'Se esperaba un booleano (true, false, 1, 0, yes, no), '
                    f'se recibió: "{v}"'
                )
            return v.lower() in self._BOOLEAN_TRUE
        if self.tipo_dato == self.TipoDato.DATE:
            if not self._DATE_RE.match(v):
                raise ValueError(
                    f'Se esperaba una fecha en formato YYYY-MM-DD, se recibió: "{v}"'
                )
            return date.fromisoformat(v)
        return self.valor

    def clean(self):
        """Valida que valor sea compatible con tipo_dato antes de guardar.

        Aplica las reglas de cada tipo (ver _castear_valor):
            - INTEGER: debe ser un entero no negativo.
            - BOOLEAN: debe ser un valor reconocible como verdadero/falso.
            - DATE:    debe tener formato YYYY-MM-DD.

        Raises:
            ValidationError: Con clave 'valor' si el valor no pasa la validación
                             del tipo declarado en tipo_dato.
        """
        v = (self.valor or '').strip()
        try:
            self._castear_valor(v)
        except (ValueError, TypeError) as exc:
            raise ValidationError({'valor': str(exc)})

    def save(self, *args, **kwargs):
        """Llama a full_clean() antes de guardar para forzar validación desde cualquier contexto."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_valor_casteado(self):
        """Convierte el valor almacenado al tipo Python correspondiente.

        Returns:
            int | bool | date | str: Valor convertido según tipo_dato.
        """
        return self._castear_valor(self.valor.strip())

    def __str__(self):
        return f'[{self.categoria}] {self.clave} = {self.valor}'


class IdentidadInstitucional(models.Model):
    """
    Registro único (pk=1) con la identidad institucional que usan PDF, Excel y correos.
    Se separa de ParametroSistema porque el logotipo es un archivo.
    Usar siempre IdentidadInstitucional.obtener() (o configuracion.identidad.obtener_identidad()).
    """

    NOMBRE_INSTITUCION_DEFECTO = 'UFPS — Plataforma ABP'
    PROGRAMA_ACADEMICO_DEFECTO = 'Ingeniería de Sistemas'

    nombre_institucion = models.CharField(max_length=200)
    programa_academico = models.CharField(max_length=200)
    logotipo = models.FileField(upload_to='identidad/', null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    id_usuario_actualiza = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='identidades_actualizadas',
        db_column='id_usuario_actualiza_id',
    )

    class Meta:
        db_table = 'identidad_institucional'
        verbose_name = 'Identidad institucional'
        verbose_name_plural = 'Identidad institucional'

    @classmethod
    def obtener(cls):
        """
        Retorna el registro único, creándolo si no existe.
        Valores iniciales: ParametroSistema (nombre_institucion, nombre_programa)
        si existen y no están vacíos; si no, las constantes por defecto.
        """
        identidad, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'nombre_institucion': cls._valor_parametro(
                    'nombre_institucion', cls.NOMBRE_INSTITUCION_DEFECTO
                ),
                'programa_academico': cls._valor_parametro(
                    'nombre_programa', cls.PROGRAMA_ACADEMICO_DEFECTO
                ),
            },
        )
        return identidad

    @staticmethod
    def _valor_parametro(clave, defecto):
        valor = (
            ParametroSistema.objects.filter(clave=clave)
            .values_list('valor', flat=True)
            .first()
        )
        return valor.strip() if valor and valor.strip() else defecto

    def __str__(self):
        return f'{self.nombre_institucion} — {self.programa_academico}'
