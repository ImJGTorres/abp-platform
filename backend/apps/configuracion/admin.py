from django.contrib import admin

from .models import ParametroSistema


@admin.register(ParametroSistema)
class ParametroSistemaAdmin(admin.ModelAdmin):
    list_display  = ('clave', 'categoria', 'tipo_dato', 'valor', 'usuario_modifico', 'fecha_actualizacion')
    list_filter   = ('categoria', 'tipo_dato')
    search_fields = ('clave', 'descripcion')
    readonly_fields = ('fecha_actualizacion',)
