# Para poblar la tabla con los parámetros iniciales ejecutar:
#   python manage.py loaddata parametros_iniciales
# Este comando carga los datos iniciales desde un archivo fixture JSON/YAML

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
        on_delete=models.PROTECT,
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

    # Permite organizar los parámetros en grupos lógicos para la API
    class Categoria(models.TextChoices):
        INSTITUCIONAL = 'institucional', 'Institucional'
        SEGURIDAD     = 'seguridad',     'Seguridad'
        ARCHIVOS      = 'archivos',      'Archivos'
        SESIONES      = 'sesiones',      'Sesiones'
        GENERAL       = 'general',       'General'

    # Define qué tipo de valor puede almacenar cada parámetro
    class TipoDato(models.TextChoices):
        STRING  = 'string',  'Texto'
        INTEGER = 'integer', 'Entero'
        BOOLEAN = 'boolean', 'Booleano'
        DATE    = 'date',    'Fecha'

    # Constantes privadas para validación de booleanos
    # Se usan en clean() para validar y en get_valor_casteado() para convertir
    _BOOLEAN_TRUE  = {'true', '1', 'yes'}
    _BOOLEAN_FALSE = {'false', '0', 'no'}

    # _DATE_RE: Expresión regular para validar formato de fecha YYYY-MM-DD
    # Se usa en clean() para verificar que la fecha tenga el formato correcto
    _DATE_RE       = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    # === CAMPOS DEL MODELO ===

    # clave: Identificador único del parámetro (ej: "max_estudiantes_por_equipo")
    # unique=True asegura que no haya dos parámetros con la misma clave
    clave = models.CharField(max_length=100, unique=True)

    # valor: Valor del parámetro almacenado como texto (string)
    # Se guarda como texto para flexibilidad y se castea según tipo_dato
    valor = models.TextField()

    # descripcion: Descripción opcional del parámetro para documentación
    descripcion = models.TextField(null=True, blank=True)

    # categoria: Grupo al que pertenece el parámetro (institucional, seguridad, etc.)
    # Usado para agrupar los parámetros en la respuesta API
    categoria = models.CharField(max_length=50, choices=Categoria.choices)

    # tipo_dato: Define cómo debe interpretarse el valor (string, integer, boolean, date)
    # Importante para la validación y el casteado de valores
    tipo_dato = models.CharField(max_length=20, choices=TipoDato.choices)

    # fecha_actualizacion: Fecha y hora del último cambio al parámetro
    # auto_now=True: Se actualiza automáticamente cada vez que se guarda
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # usuario_modifico: Referencia al usuario que realizó la última modificación
    # SET_NULL: Si se elimina el usuario, el campo queda como NULL
    # Permite auditoría de quién cambió cada parámetro
    usuario_modifico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'parametro_sistema'
        # ordering: Ordena los resultados por categoría y luego por clave
        ordering = ['categoria', 'clave']

    def clean(self):
        """Valida que `valor` sea compatible con `tipo_dato` antes de guardar.
        
        Este método es llamado automáticamente por save() y por el admin de Django.
        Valida que el valor proporcionado coincida con el tipo de dato declarado.
        Si la validación falla, lanza ValidationError que evita guardar datos inválidos.
        
        Tipos de validación:
        - INTEGER: Verifica que el valor sea un número entero válido
        - BOOLEAN: Acepta true/false/1/0/yes/no (insensible a mayúsculas)
        - DATE: Verifica formato YYYY-MM-DD y que sea una fecha real
        - STRING: Siempre pasa la validación (sin restricciones)
        """
        v = (self.valor or '').strip()  # Obtiene el valor sin espacios al inicio/fin

        # Validación para tipo INTEGER
        # Verifica que el valor pueda convertirse a entero (rechaza texto como "abc")
        if self.tipo_dato == self.TipoDato.INTEGER:
            try:
                int(v)  # Intenta convertir a entero
            except ValueError:
                raise ValidationError(
                    {'valor': f'Se esperaba un entero, se recibió: "{v}"'}
                )

        # Validación para tipo BOOLEAN
        # Solo acepta valores definidos en _BOOLEAN_TRUE o _BOOLEAN_FALSE
        elif self.tipo_dato == self.TipoDato.BOOLEAN:
            if v.lower() not in self._BOOLEAN_TRUE | self._BOOLEAN_FALSE:
                raise ValidationError(
                    {'valor': f'Se esperaba true/false/1/0/yes/no, se recibió: "{v}"'}
                )

        # Validación para tipo DATE
        # Primero verifica el formato con regex, luego valida que sea fecha real
        elif self.tipo_dato == self.TipoDato.DATE:
            # Verifica que coincida con formato YYYY-MM-DD
            if not self._DATE_RE.match(v):
                raise ValidationError(
                    {'valor': f'Se esperaba formato YYYY-MM-DD, se recibió: "{v}"'}
                )
            try:
                date.fromisoformat(v)  # Valida que sea una fecha válida (no "2026-02-30")
            except ValueError:
                raise ValidationError({'valor': f'Fecha inválida: "{v}"'})

    def save(self, *args, **kwargs):
        """Sobrescribe el método save() para ejecutar validación antes de guardar.
        
        Llama a full_clean() que a su vez ejecuta clean() y las validaciones de Django.
        Esto asegura que la validación funcione tanto desde el admin de Django
        como desde código (ej: desde la API o shell de Django).
        
        Si la validación falla, se lanza ValidationError y no se guarda nada.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def get_valor_casteado(self):
        """Convierte el valor almacenado (como string) al tipo correcto de Python.
        
        Returns:
            - int: Si tipo_dato es 'integer' (ej: "5" → 5)
            - bool: Si tipo_dato es 'boolean' (ej: "true" → True)
            - date: Si tipo_dato es 'date' (ej: "2026-04-08" → date(2026,4,8))
            - str: Si tipo_dato es 'string' (retorna el valor como está)
        
        Este método se usa en el serializador para exponer 'valor_casteado' en la API.
        Permite que los clientes reciban el valor ya convertido al tipo correcto.
        """
        v = self.valor.strip()
        
        # Convierte a entero: "30" → 30
        if self.tipo_dato == self.TipoDato.INTEGER:
            return int(v)
        
        # Convierte a booleano: "true" → True, "false" → False
        if self.tipo_dato == self.TipoDato.BOOLEAN:
            return v.lower() in self._BOOLEAN_TRUE
        
        # Convierte a fecha: "2026-04-08" → date(2026, 4, 8)
        if self.tipo_dato == self.TipoDato.DATE:
            return date.fromisoformat(v)
        
        # Para strings, retorna el valor tal cual
        return self.valor

    def __str__(self):
        """Representación en string del objeto para debugging y admin de Django.
        
        Muestra: [categoría] clave = valor
        Ejemplo: [general] max_estudiantes_por_equipo = 5
        """
        return f'[{self.categoria}] {self.clave} = {self.valor}'
