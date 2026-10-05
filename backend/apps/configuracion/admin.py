from django.contrib import admin

from .models import IdentidadInstitucional, ParametroSistema


@admin.register(ParametroSistema)
class ParametroSistemaAdmin(admin.ModelAdmin):
    list_display  = ('clave', 'categoria', 'tipo_dato', 'valor', 'usuario_modifico', 'fecha_actualizacion')
    list_filter   = ('categoria', 'tipo_dato')
    search_fields = ('clave', 'descripcion')
    readonly_fields = ('fecha_actualizacion',)


@admin.register(IdentidadInstitucional)
class IdentidadInstitucionalAdmin(admin.ModelAdmin):
    list_display    = ('nombre_institucion', 'programa_academico', 'logotipo', 'id_usuario_actualiza', 'fecha_actualizacion')
    readonly_fields = ('id_usuario_actualiza', 'fecha_actualizacion')

    def has_add_permission(self, request):
        # Registro único: se crea con IdentidadInstitucional.obtener()
        return not IdentidadInstitucional.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.pk = 1
        obj.id_usuario_actualiza = request.user
        super().save_model(request, obj, form, change)
