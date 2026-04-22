from django.db import models


# Modelo que representa un equipo de estudiantes dentro de un proyecto.
# Tabla de equipos con FK a proyecto, nombre, descripción, cupo máximo y estado.
class Equipo(models.Model):
    # Proyecto al que pertenece este equipo.
    # related_name='equipos' permite acceder a todos los equipos de un proyecto: proyecto.equipos.all()
    proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        related_name='equipos',
    )
    # Nombre del equipo (únido dentro del proyecto).
    nombre = models.CharField(max_length=100)
    # Descripción opcional del propósito o temática del equipo.
    descripcion = models.TextField(blank=True, default='')
    # Cantidad máxima de integrantes que puede tener el equipo.
    # Se valida contra el parámetro del sistema max_estudiantes_por_equipo.
    cupo_maximo = models.PositiveIntegerField()
    # Fecha automática de creación del equipo (se establece al crear).
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # Estado del equipo: activo (vigente) o inactivo.
    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo',
    )

    class Meta:
        # Restricción de nombre único por proyecto.
        # Evita que existan dos equipos con el mismo nombre dentro de un mismo proyecto.
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'proyecto'],
                name='unique_nombre_por_proyecto',
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.proyecto})"


# Modelo para representar la membresía de un usuario en un equipo.
# Relaciona usuarios con equipos y define su rol interno.
# Un usuario puede pertenecer a varios equipos (en diferentes proyectos) pero solo un equipo por proyecto.
class MiembroEquipo(models.Model):
    # Equipo al que pertenece este miembro.
    # related_name='miembros' permite acceder a los miembros desde un equipo: equipo.miembros.all()
    equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.CASCADE,
        related_name='miembros',
    )
    # Usuario miembro del equipo.
    # related_name='membresías' permite acceder a las membresías desde un usuario: usuario.membresías.all()
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='membresías',
    )
    # Fecha automática cuando el miembro se asigna al equipo.
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    # Estado de la membresía: activo (vigente) o retirado (ya no participa).
    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('retirado', 'Retirado')],
        default='activo',
    )
    # Rol interno del miembro dentro del equipo.
    # Define la función específica que cumple: líder, desarrollador, diseñador, tester o analista.
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
    # Descripción textual de las responsabilidades específicas del miembro en el equipo.
    descripcion_responsabilidades = models.TextField(blank=True, default='')

    class Meta:
        # Restricción de unicidad: un usuario solo puede tener una membresía por equipo.
        # Evita duplicar la misma relación equipo-usuario.
        constraints = [
            models.UniqueConstraint(
                fields=['equipo', 'usuario'],
                name='unique_usuario_por_equipo',
            )
        ]

    def __str__(self):
        return f"{self.usuario} en {self.equipo}"
