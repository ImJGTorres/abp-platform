from django.db import models


class Equipo(models.Model):
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

    def __str__(self):
        return f"{self.nombre} ({self.proyecto})"


class MiembroEquipo(models.Model):
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

    def __str__(self):
        return f"{self.usuario} en {self.equipo}"
