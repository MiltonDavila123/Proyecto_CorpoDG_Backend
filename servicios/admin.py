from django.contrib import admin
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Mensaje


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


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'pais', 'precio_desde', 'destacado', 'activo', 'fecha_creacion']
    list_filter = ['destacado', 'activo', 'pais']
    search_fields = ['nombre', 'pais', 'descripcion']
    list_editable = ['destacado', 'activo']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'destino', 'estrellas', 'precio_noche', 'disponible', 'fecha_creacion']
    list_filter = ['estrellas', 'disponible', 'destino']
    search_fields = ['nombre', 'descripcion', 'direccion', 'destino__nombre']
    list_editable = ['disponible']
    autocomplete_fields = ['destino']


@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    list_display = ['aerolinea', 'origen', 'destino', 'tipo_vuelo', 'duracion', 'precio', 'moneda', 'disponible']
    list_filter = ['tipo_vuelo', 'disponible', 'aerolinea', 'origen', 'destino']
    search_fields = ['aerolinea', 'origen', 'destino']
    list_editable = ['disponible']


@admin.register(RentaAuto)
class RentaAutoAdmin(admin.ModelAdmin):
    list_display = ['marca', 'modelo', 'tipo', 'ano', 'precio_dia', 'ubicacion', 'disponible']
    list_filter = ['tipo', 'transmision', 'disponible', 'marca']
    search_fields = ['marca', 'modelo', 'ubicacion']
    list_editable = ['disponible']


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'asunto', 'fecha_envio', 'leido', 'respondido']
    list_filter = ['leido', 'respondido', 'fecha_envio']
    search_fields = ['nombre', 'email', 'asunto', 'mensaje']
    list_editable = ['leido', 'respondido']
    readonly_fields = ['fecha_envio']
