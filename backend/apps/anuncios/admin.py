from django.contrib import admin

from .models import Anuncio


@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display    = ('titulo', 'id_curso', 'id_proyecto', 'id_autor', 'fecha_publicacion')
    list_filter     = ('id_curso', 'id_proyecto')
    search_fields   = ('titulo', 'mensaje')
    readonly_fields = ('fecha_creacion',)
