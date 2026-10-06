from django.contrib import admin

from .models import Alerta, ColaCorreo


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display    = ('tipo', 'gravedad', 'id_usuario_destino', 'estado', 'fecha_generacion')
    list_filter     = ('tipo', 'gravedad', 'estado')
    search_fields   = ('mensaje',)
    readonly_fields = ('fecha_generacion',)


@admin.register(ColaCorreo)
class ColaCorreoAdmin(admin.ModelAdmin):
    list_display    = ('plantilla', 'id_usuario_destino', 'asunto', 'estado', 'fecha_creacion', 'fecha_envio')
    list_filter     = ('plantilla', 'estado')
    search_fields   = ('asunto',)
    readonly_fields = ('fecha_creacion',)
