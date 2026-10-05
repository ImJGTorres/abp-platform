from django.db import models
from django.utils import timezone


class Anuncio(models.Model):
    """Anuncio del muro de un curso o de un proyecto (HU-039)."""

    id_curso = models.ForeignKey(
        'cursos.Curso',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='anuncios',
        db_column='id_curso_id',
    )
    id_proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='anuncios',
        db_column='id_proyecto_id',
    )
    id_autor = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='anuncios_publicados',
        db_column='id_autor_id',
    )
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha_publicacion = models.DateTimeField(default=timezone.now)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'anuncio'
        ordering = ['-fecha_publicacion']
        constraints = [
            models.CheckConstraint(
                check=models.Q(id_curso__isnull=False) | models.Q(id_proyecto__isnull=False),
                name='anuncio_curso_o_proyecto',
            )
        ]

    def __str__(self):
        return f"{self.titulo} ({self.id_autor_id})"
