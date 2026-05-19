from django.core.exceptions import ValidationError
from django.db import models


class Equipo(models.Model):
    """Representa un equipo de estudiantes dentro de un proyecto."""

    proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        related_name='equipos',
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')
    cupo_maximo = models.PositiveIntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'proyecto'],
                name='unique_nombre_por_proyecto',
            )
        ]

    def clean(self):
        """Valida que cupo_maximo no supere el parámetro del sistema.

        Raises:
            ValidationError: Si cupo_maximo excede max_estudiantes_por_equipo o si
                el parámetro no existe en la configuración del sistema.
        """
        if not self.cupo_maximo:
            return
        try:
            from apps.configuracion.models import ParametroSistema
            parametro = ParametroSistema.objects.get(clave='max_estudiantes_por_equipo')
            max_val = int(parametro.valor)
        except ParametroSistema.DoesNotExist:
            raise ValidationError(
                {'cupo_maximo': 'No se encontró el parámetro max_estudiantes_por_equipo en la configuración del sistema.'}
            )
        if self.cupo_maximo > max_val:
            raise ValidationError(
                {'cupo_maximo': f'El cupo máximo no puede superar {max_val} estudiantes por equipo.'}
            )

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.proyecto})"


class MiembroEquipo(models.Model):
    """Representa la membresía de un usuario en un equipo.

    El historial se preserva mediante soft-delete: al retirar un estudiante,
    su registro queda con estado='retirado'. Las reasignaciones crean un nuevo
    registro, permitiendo auditar el recorrido completo de cada estudiante.
    """

    equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.CASCADE,
        related_name='miembros',
    )
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='membresías',
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('retirado', 'Retirado')],
        default='activo',
    )
    rol_interno = models.CharField(
        max_length=20,
        choices=[
            ('lider', 'Líder'),
            ('desarrollador', 'Desarrollador'),
            ('disenador', 'Diseñador'),
            ('tester', 'Tester'),
            ('analista', 'Analista'),
        ],
        blank=True,
        default='',
    )
    descripcion_responsabilidades = models.TextField(blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['equipo', 'usuario'],
                name='unique_usuario_por_equipo',
            )
        ]

    def clean(self):
        """Valida unicidad de equipo por proyecto y cupo máximo al crear.

        Solo se ejecuta en creación (pk is None). Las actualizaciones de estado
        o rol no requieren re-validar estas reglas de negocio.

        Raises:
            ValidationError: Si el usuario ya pertenece a otro equipo activo en el
                mismo proyecto, o si el equipo ha alcanzado su cupo máximo.
        """
        if self.pk is not None or not self.equipo_id or not self.usuario_id:
            return
        proyecto = self.equipo.proyecto
        ya_en_proyecto = MiembroEquipo.objects.filter(
            usuario_id=self.usuario_id,
            estado='activo',
            equipo__proyecto=proyecto,
        ).exclude(equipo=self.equipo).exists()
        if ya_en_proyecto:
            raise ValidationError("El estudiante ya pertenece a otro equipo en este proyecto.")
        miembros_activos = MiembroEquipo.objects.filter(
            equipo=self.equipo,
            estado='activo',
        ).count()
        if miembros_activos >= self.equipo.cupo_maximo:
            raise ValidationError(
                f"El equipo ha alcanzado su cupo máximo de {self.equipo.cupo_maximo} integrantes."
            )

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario} en {self.equipo}"
