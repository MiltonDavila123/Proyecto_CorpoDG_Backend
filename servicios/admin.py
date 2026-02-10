from django.contrib import admin
from django import forms
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Region, PaisRegion, Ciudad, Aerolinea, PaqueteTuristico


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
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'pdf_url':
            field.label = 'PDF URL (opcional)'
        elif db_field.name == 'mensaje_reserva':
            field.label = 'Mensaje reserva (opcional)'
        return field


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'destino', 'estrellas', 'precio_noche', 'disponible', 'fecha_creacion']
    list_filter = ['estrellas', 'disponible', 'destino']
    search_fields = ['nombre', 'descripcion', 'direccion', 'destino__nombre']
    list_editable = ['disponible']
    autocomplete_fields = ['destino']
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'pdf_url':
            field.label = 'PDF URL (opcional)'
        elif db_field.name == 'mensaje_reserva':
            field.label = 'Mensaje reserva (opcional)'
        return field


@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    list_display = ['aerolinea', 'origen', 'destino', 'tipo_vuelo', 'numero_vuelo', 'duracion', 'precio', 'moneda', 'disponible']
    list_filter = ['tipo_vuelo', 'disponible', 'aerolinea', 'origen__pais__region', 'destino__pais__region']
    search_fields = ['aerolinea__nombre', 'origen__nombre', 'destino__nombre', 'numero_vuelo']
    list_editable = ['disponible']
    autocomplete_fields = ['aerolinea', 'origen', 'destino']


@admin.register(RentaAuto)
class RentaAutoAdmin(admin.ModelAdmin):
    list_display = ['marca', 'modelo', 'tipo', 'ano', 'precio_dia', 'ciudad', 'disponible']
    list_filter = ['tipo', 'transmision', 'disponible', 'marca', 'ciudad__pais__region']
    search_fields = ['marca', 'modelo', 'ciudad__nombre', 'ciudad__pais__nombre']
    list_editable = ['disponible']
    autocomplete_fields = ['ciudad']


# =====================================================
# ADMIN PARA PAQUETES TURÍSTICOS
# =====================================================

class PaisRegionInline(admin.TabularInline):
    """Inline para agregar países directamente desde la región"""
    model = PaisRegion
    extra = 3
    fields = ['nombre', 'codigo_pais', 'bandera_url', 'activo']


class CiudadInline(admin.TabularInline):
    """Inline para agregar ciudades directamente desde el país"""
    model = Ciudad
    extra = 3
    fields = ['nombre', 'codigo_aeropuerto', 'es_capital', 'imagen_url', 'activo']


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['get_nombre_display', 'descripcion_corta', 'cantidad_paises', 'orden', 'activo']
    list_filter = ['activo', 'nombre']
    list_editable = ['orden', 'activo']
    search_fields = ['nombre', 'descripcion']
    inlines = [PaisRegionInline]
    
    def get_nombre_display(self, obj):
        return obj.get_nombre_display()
    get_nombre_display.short_description = 'Región'
    
    def descripcion_corta(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
        return '-'
    descripcion_corta.short_description = 'Descripción'
    
    def cantidad_paises(self, obj):
        return obj.paises.count()
    cantidad_paises.short_description = 'Países/Destinos'


@admin.register(PaisRegion)
class PaisRegionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'region', 'codigo_pais', 'cantidad_ciudades', 'activo']
    list_filter = ['region', 'activo']
    search_fields = ['nombre', 'region__nombre']
    list_editable = ['activo']
    inlines = [CiudadInline]
    
    def cantidad_ciudades(self, obj):
        return obj.ciudades.count()
    cantidad_ciudades.short_description = 'Ciudades'


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'pais', 'get_region', 'codigo_aeropuerto', 'es_capital', 'activo']
    list_filter = ['pais__region', 'pais', 'es_capital', 'activo']
    search_fields = ['nombre', 'pais__nombre', 'codigo_aeropuerto']
    list_editable = ['es_capital', 'activo']
    autocomplete_fields = ['pais']
    
    def get_region(self, obj):
        return obj.pais.region.get_nombre_display()
    get_region.short_description = 'Región'
    get_region.admin_order_field = 'pais__region'


@admin.register(Aerolinea)
class AerolineaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_iata', 'pais_origen', 'cantidad_vuelos', 'activo']
    list_filter = ['activo', 'pais_origen']
    search_fields = ['nombre', 'codigo_iata', 'pais_origen']
    list_editable = ['activo']
    
    def cantidad_vuelos(self, obj):
        return obj.vuelos.count()
    cantidad_vuelos.short_description = 'Vuelos'


@admin.register(PaqueteTuristico)
class PaqueteTuristicoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'region', 'pais_destino', 'precio', 'duracion_dias', 'duracion_noches', 'tipo_paquete', 'destacado', 'activo']
    list_filter = ['region', 'tipo_paquete', 'temporada', 'destacado', 'activo', 'aerolinea']
    search_fields = ['titulo', 'titulo_detalle', 'descripcion_corta', 'descripcion_extensa', 'pais_destino__nombre']
    list_editable = ['destacado', 'activo']
    autocomplete_fields = ['aerolinea']  # Solo aerolinea, los demás usan filtros dinámicos
    date_hierarchy = 'fecha_creacion'
    
    class Media:
        js = ('servicios/js/paquete_filtros.js',)
    
    fieldsets = (
        ('Información del Card (Vista previa)', {
            'fields': (
                'titulo',
                'subtitulo',
                'imagen_url',
                'descripcion_corta',
            )
        }),
        ('Ubicación y Destino', {
            'fields': (
                'region',
                'pais_destino',
                'ciudad_destino',
            )
        }),
        ('Precios y Tipo', {
            'fields': (
                ('precio', 'moneda'),
                'tipo_paquete',
            )
        }),
        ('Duración, Fechas y Aerolínea', {
            'fields': (
                ('duracion_dias', 'duracion_noches'),
                'salidas',
                'fecha_salidas_texto',
                'aerolinea',
            )
        }),
        ('El Paquete Incluye (Iconos)', {
            'fields': (
                ('incluye_vuelo', 'incluye_hotel', 'incluye_alimentacion'),
                ('incluye_traslados', 'incluye_tours', 'incluye_seguro'),
            ),
            'classes': ('collapse',),
        }),
        ('Información Detallada (Página del paquete)', {
            'fields': (
                'titulo_detalle',
                'descripcion_extensa',
            ),
            'classes': ('collapse',),
        }),
        ('Detalles del Paquete (Sidebar)', {
            'fields': (
                'temporada',
                'tipo_viaje',
                ('precio_aplica_desde', 'precio_aplica_hasta'),
            ),
            'classes': ('collapse',),
        }),
        ('Información del Destino (Sidebar)', {
            'fields': (
                'ubicacion_mapa_url',
                'idioma',
                'moneda_local',
                'lugares_destacados',
                'documentos_requeridos',
                'temperatura',
            ),
            'classes': ('collapse',),
        }),
        ('Programa Incluye', {
            'fields': ('programa_incluye',),
            'classes': ('collapse',),
        }),
        ('No Incluye', {
            'fields': ('no_incluye',),
            'classes': ('collapse',),
        }),
        ('Cómo Reservar', {
            'fields': ('como_reservar',),
            'classes': ('collapse',),
        }),
        ('Importante', {
            'fields': ('importante',),
            'classes': ('collapse',),
        }),
        ('Horarios de Vuelo', {
            'fields': ('horarios_vuelo',),
            'classes': ('collapse',),
        }),
        ('Políticas de Equipaje', {
            'fields': ('politicas_equipaje',),
            'classes': ('collapse',),
        }),
        ('Requisitos de Viaje', {
            'fields': ('requisitos_viaje',),
            'classes': ('collapse',),
        }),
        ('Formas de Pago', {
            'fields': ('formas_pago',),
            'classes': ('collapse',),
        }),
        ('Política de Cancelación', {
            'fields': ('politica_cancelacion',),
            'classes': ('collapse',),
        }),
        ('PDF y Contacto', {
            'fields': (
                'pdf_url',
                'mensaje_reserva',
            ),
            'classes': ('collapse',),
        }),
        ('Estado', {
            'fields': (
                ('destacado', 'activo'),
            )
        }),
    )
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'pdf_url':
            field.label = 'PDF URL (Google Drive)'
        return field
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra los países y ciudades activos"""
        if db_field.name == 'pais_destino':
            kwargs['queryset'] = PaisRegion.objects.filter(activo=True)
        elif db_field.name == 'ciudad_destino':
            kwargs['queryset'] = Ciudad.objects.filter(activo=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
