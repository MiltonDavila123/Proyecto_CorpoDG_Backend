from django.contrib import admin
from .models import Cliente, Solicitud


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'email', 'telefono', 'fecha_registro']
    search_fields = ['nombre_completo', 'email', 'telefono']
    list_filter = ['fecha_registro']


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'mensaje_corto', 'fecha_creacion', 'atendido']
    list_filter = ['atendido', 'fecha_creacion']
    search_fields = ['cliente__nombre_completo', 'cliente__email', 'mensaje']
    
    def mensaje_corto(self, obj):
        return obj.mensaje[:50] + '...' if len(obj.mensaje) > 50 else obj.mensaje
    mensaje_corto.short_description = 'Mensaje'
