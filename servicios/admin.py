from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
import re
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Region, PaisRegion, Ciudad, Aerolinea, Aeropuerto, PaqueteTuristico


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


from django.contrib.admin import site as admin_site
from django.contrib.admin.widgets import AutocompleteSelect

class VueloAdminForm(forms.ModelForm):
    """Form personalizado para vuelos"""
    
    ciudad_origen_filtro = forms.ModelChoiceField(
        queryset=Ciudad.objects.all(), 
        required=False, 
        label="Ciudad Origen (Filtro)",
        widget=AutocompleteSelect(Aeropuerto._meta.get_field('ciudad'), admin_site)
    )
    
    ciudad_destino_filtro = forms.ModelChoiceField(
        queryset=Ciudad.objects.all(), 
        required=False, 
        label="Ciudad Destino (Filtro)",
        widget=AutocompleteSelect(Aeropuerto._meta.get_field('ciudad'), admin_site)
    )

    class Meta:
        model = Vuelo
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Para Origen y Destino, nacen vacíos para evitar ralentizar la página (cargar miles de aeropuertos de golpe).
        # Serán poblados únicamente por el Javascript mediante la búsqueda por ciudad.
        # Solo se carga el seleccionado actualmente si existe una instancia (para edición).
        if self.instance and self.instance.pk:
            if self.instance.origen:
                self.fields['origen'].queryset = Aeropuerto.objects.filter(pk=self.instance.origen.pk)
            else:
                self.fields['origen'].queryset = Aeropuerto.objects.none()
                
            if self.instance.destino:
                self.fields['destino'].queryset = Aeropuerto.objects.filter(pk=self.instance.destino.pk)
            else:
                self.fields['destino'].queryset = Aeropuerto.objects.none()
                
        elif hasattr(self, 'data') and self.data:
            # En POST, validamos con lo enviado
            if self.data.get('origen'):
                self.fields['origen'].queryset = Aeropuerto.objects.filter(pk=self.data.get('origen'))
            else:
                self.fields['origen'].queryset = Aeropuerto.objects.none()
                
            if self.data.get('destino'):
                self.fields['destino'].queryset = Aeropuerto.objects.filter(pk=self.data.get('destino'))
            else:
                self.fields['destino'].queryset = Aeropuerto.objects.none()
        else:
            self.fields['origen'].queryset = Aeropuerto.objects.none()
            self.fields['destino'].queryset = Aeropuerto.objects.none()


@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    form = VueloAdminForm
    list_display = ['aerolinea', 'origen', 'destino', 'duracion', 'precio', 'moneda', 'destacado', 'disponible']
    list_filter = ['destacado', 'disponible', 'aerolinea', 'origen__pais__region', 'destino__pais__region']
    search_fields = ['aerolinea__nombre', 'origen__nombre', 'destino__nombre', 'origen__codigo_iata', 'destino__codigo_iata']
    list_editable = ['destacado', 'disponible']
    autocomplete_fields = ['aerolinea']
    
    fieldsets = (
        ('Selección de Origen', {
            'fields': ('ciudad_origen_filtro', 'origen'),
            'description': 'Busca una ciudad para autocompletar el aeropuerto con los de su país (opcional).'
        }),
        ('Selección de Destino', {
            'fields': ('ciudad_destino_filtro', 'destino'),
            'description': 'Busca una ciudad para autocompletar el aeropuerto con los de su país (opcional).'
        }),
        ('Detalles del Vuelo', {
            'fields': ('aerolinea', 'duracion', 'precio', 'moneda', 'imagen_url', 'mensaje_reserva')
        }),
        ('Estado', {
            'fields': ('destacado', 'disponible')
        }),
    )

    class Media:
        js = ('servicios/js/vuelo_filtros.js',)


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
    extra = 1
    fields = ['nombre', 'nombre_en', 'codigo_iso', 'codigo_iso3', 'capital', 'bandera_svg', 'activo']
    show_change_link = True


class CiudadInline(admin.TabularInline):
    """Inline para agregar ciudades directamente desde el país"""
    model = Ciudad
    extra = 1
    fields = ['nombre', 'codigo_ciudad', 'latitud', 'longitud', 'es_capital', 'activo']
    show_change_link = True


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
    list_display = ['nombre', 'region', 'codigo_iso', 'capital', 'cantidad_ciudades', 'activo']
    list_filter = ['region', 'activo']
    search_fields = ['nombre', 'nombre_en', 'codigo_iso', 'codigo_iso3', 'capital', 'region__nombre']
    list_editable = ['activo']
    inlines = [CiudadInline]
    readonly_fields = ['bandera_preview']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('region', 'nombre', 'nombre_en', 'capital')
        }),
        ('Códigos ISO', {
            'fields': ('codigo_iso', 'codigo_iso3')
        }),
        ('Banderas', {
            'fields': ('bandera_png', 'bandera_svg', 'bandera_preview'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def cantidad_ciudades(self, obj):
        return obj.ciudades.count()
    cantidad_ciudades.short_description = 'Ciudades'
    
    def bandera_preview(self, obj):
        if obj.bandera_svg or obj.bandera_png:
            url = obj.bandera_svg or obj.bandera_png
            return format_html('<img src="{}" style="max-height: 30px; max-width: 50px;" />', url)
        return '-'
    bandera_preview.short_description = 'Vista previa'


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'pais', 'get_region', 'codigo_ciudad', 'es_capital', 'coordenadas', 'activo']
    list_filter = ['pais__region', 'pais', 'es_capital', 'activo']
    search_fields = ['nombre', 'pais__nombre', 'codigo_ciudad']
    list_editable = ['es_capital', 'activo']
    autocomplete_fields = ['pais']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('pais', 'nombre', 'codigo_ciudad', 'es_capital')
        }),
        ('Coordenadas', {
            'fields': ('latitud', 'longitud'),
            'classes': ('collapse',)
        }),
        ('Otros', {
            'fields': ('imagen_url', 'activo'),
            'classes': ('collapse',)
        }),
    )
    
    def get_region(self, obj):
        return obj.pais.region.get_nombre_display()
    get_region.short_description = 'Región'
    get_region.admin_order_field = 'pais__region'
    
    def coordenadas(self, obj):
        if obj.latitud and obj.longitud:
            return f"{obj.latitud:.4f}, {obj.longitud:.4f}"
        return '-'
    coordenadas.short_description = 'Coordenadas'


@admin.register(Aerolinea)
class AerolineaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_iata', 'codigo_icao', 'pais_origen', 'anio_creacion', 'logo_preview', 'cantidad_vuelos', 'activo']
    list_filter = ['activo', 'pais_origen']
    search_fields = ['nombre', 'codigo_iata', 'codigo_icao', 'pais_origen', 'base_aeropuerto']
    list_editable = ['activo']
    
    def get_readonly_fields(self, request, obj=None):
        """Solo mostrar previews cuando el objeto ya existe"""
        if obj:
            return ['logo_preview', 'brandmark_preview']
        return []
    
    def get_fieldsets(self, request, obj=None):
        """Fieldsets dinámicos: con preview al editar, sin preview al crear"""
        fieldsets = [
            ('Información Básica', {
                'fields': ('nombre', 'codigo_iata', 'codigo_icao', 'pais_origen')
            }),
            ('Detalles', {
                'fields': ('anio_creacion', 'base_aeropuerto', 'sitio_web')
            }),
        ]
        
        if obj:
            # Editando: mostrar logos con preview
            fieldsets.append(('Logos', {
                'fields': ('logo_url', 'logo_preview', 'brandmark_url', 'brandmark_preview'),
            }))
        else:
            # Creando: solo campos de URL
            fieldsets.append(('Logos', {
                'fields': ('logo_url', 'brandmark_url'),
            }))
        
        fieldsets.append(('Estado', {
            'fields': ('activo',)
        }))
        
        return fieldsets
    
    def cantidad_vuelos(self, obj):
        return obj.vuelos.count()
    cantidad_vuelos.short_description = 'Vuelos'
    
    def logo_preview(self, obj):
        if obj.logo_url:
            return format_html('<img src="{}" style="max-height: 30px; max-width: 120px;" />', obj.logo_url)
        return '-'
    logo_preview.short_description = 'Logo'
    
    def brandmark_preview(self, obj):
        if obj.brandmark_url:
            return format_html('<img src="{}" style="max-height: 30px; max-width: 50px;" />', obj.brandmark_url)
        return '-'
    brandmark_preview.short_description = 'Brandmark'


@admin.register(Aeropuerto)
class AeropuertoAdmin(admin.ModelAdmin):
    list_display = ['codigo_iata', 'codigo_icao', 'nombre', 'get_ciudad', 'pais', 'zona_horaria', 'activo']
    list_filter = ['activo', 'pais__region', 'pais']
    search_fields = ['codigo_iata', 'codigo_icao', 'nombre', 'nombre_ciudad', 'pais__nombre', 'ciudad__nombre']
    list_editable = ['activo']
    autocomplete_fields = ['ciudad', 'pais']
    
    fieldsets = (
        ('Códigos', {
            'fields': ('codigo_iata', 'codigo_icao')
        }),
        ('Información Básica', {
            'fields': ('nombre', 'pais', 'ciudad', 'nombre_ciudad', 'region')
        }),
        ('Ubicación Geográfica', {
            'fields': ('latitud', 'longitud', 'elevacion_ft', 'zona_horaria'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def get_ciudad(self, obj):
        if obj.ciudad:
            return obj.ciudad.nombre
        return obj.nombre_ciudad or '-'
    get_ciudad.short_description = 'Ciudad'
    get_ciudad.admin_order_field = 'ciudad__nombre'


class PaqueteTuristicoAdminForm(forms.ModelForm):
    """Form personalizado para validar restricciones del PaqueteTuristico"""
    
    class Meta:
        model = PaqueteTuristico
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # LOGICA PARA QUE DJANGO ACEPTE LOS DATOS DEL AJAX
        
        # 1. Manejo de PAÍS
        # Si hay datos POST (al guardar), cargamos el país seleccionado
        if self.data and self.data.get('pais_destino'):
            try:
                pais_id = int(self.data.get('pais_destino'))
                self.fields['pais_destino'].queryset = PaisRegion.objects.filter(pk=pais_id)
            except (ValueError, TypeError):
                pass # Si el dato es basura, dejamos el queryset vacío
        # Si estamos editando un registro existente, cargamos su país actual
        elif self.instance.pk and self.instance.pais_destino:
            self.fields['pais_destino'].queryset = PaisRegion.objects.filter(pk=self.instance.pais_destino.pk)
            
        # 2. Manejo de CIUDAD
        # Si hay datos POST (al guardar), cargamos la ciudad seleccionada
        if self.data and self.data.get('ciudad_destino'):
            try:
                ciudad_id = int(self.data.get('ciudad_destino'))
                self.fields['ciudad_destino'].queryset = Ciudad.objects.filter(pk=ciudad_id)
            except (ValueError, TypeError):
                pass
        # Si estamos editando, cargamos su ciudad actual
        elif self.instance.pk and self.instance.ciudad_destino:
            self.fields['ciudad_destino'].queryset = Ciudad.objects.filter(pk=self.instance.ciudad_destino.pk)
    
    def clean_pdf_url(self):
        """Valida que el PDF URL sea de Google Drive"""
        pdf_url = self.cleaned_data.get('pdf_url')
        
        # Si está vacío, está permitido
        if not pdf_url:
            return pdf_url
        
        # Validar patrón de Google Drive
        google_drive_pattern = r'^https://drive\.google\.com/file/d/[a-zA-Z0-9_-]+/(view|edit|preview)(\?.*)?$'
        
        if not re.match(google_drive_pattern, pdf_url):
            raise ValidationError(
                'El PDF debe ser un enlace válido de Google Drive. '
                'Ejemplo: https://drive.google.com/file/d/ID_DEL_ARCHIVO/view'
            )
        
        return pdf_url
    
    def clean_ubicacion_mapa_url(self):
        """Valida que la ubicación del mapa sea de OpenStreetMap"""
        ubicacion_mapa_url = self.cleaned_data.get('ubicacion_mapa_url')
        
        # Si está vacío, está permitido
        if not ubicacion_mapa_url:
            return ubicacion_mapa_url
        
        # Validar patrón de OpenStreetMap
        openstreetmap_pattern = r'^https://(www\.)?openstreetmap\.org/.*'
        
        if not re.match(openstreetmap_pattern, ubicacion_mapa_url):
            raise ValidationError(
                'La ubicación del mapa debe ser un enlace válido de OpenStreetMap. '
                'Ejemplo: https://www.openstreetmap.org/#map=11/4.6497/-74.1165'
            )
        
        return ubicacion_mapa_url


@admin.register(PaqueteTuristico)
class PaqueteTuristicoAdmin(admin.ModelAdmin):
    form = PaqueteTuristicoAdminForm
    list_display = ['titulo', 'region', 'pais_destino', 'precio', 'duracion_dias', 'duracion_noches', 'tipo_paquete', 'destacado', 'activo']
    list_filter = ['region', 'tipo_paquete', 'temporada', 'destacado', 'activo', 'aerolinea']
    search_fields = ['titulo', 'titulo_detalle', 'descripcion_corta', 'descripcion_extensa', 'pais_destino__nombre']
    list_editable = ['destacado', 'activo']
    autocomplete_fields = ['aerolinea']
    date_hierarchy = 'fecha_creacion'
    
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
        })
    )
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'pdf_url':
            field.label = 'PDF URL (Google Drive)'
        return field
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # 1. Optimización para PAÍS
        if db_field.name == 'pais_destino':
            # Si estamos editando (tenemos un objeto ID en la URL), permitimos cargar el actual
            # Si es nuevo, pasamos un queryset VACÍO para que no pese nada.
            if request.resolver_match.kwargs.get('object_id'):
                # Edición: Dejamos que Django cargue (o podrías optimizar más, pero esto es seguro)
                kwargs['queryset'] = PaisRegion.objects.filter(activo=True)
            else:
                # Creación: Queryset VACÍO. El AJAX lo llenará después.
                kwargs['queryset'] = PaisRegion.objects.none()

        # 2. Optimización para CIUDAD (La más pesada)
        elif db_field.name == 'ciudad_destino':
            if request.resolver_match.kwargs.get('object_id'):
                 # En edición, idealmente solo cargamos las ciudades del país seleccionado
                 # Pero para no complicar el backend, cargamos todo o filtramos por el objeto actual
                 # Truco: Cargar solo la ciudad seleccionada para que el form valide
                 paquete_id = request.resolver_match.kwargs.get('object_id')
                 paquete = PaqueteTuristico.objects.get(pk=paquete_id)
                 if paquete.ciudad_destino:
                     kwargs['queryset'] = Ciudad.objects.filter(pk=paquete.ciudad_destino.pk)
                 else:
                     kwargs['queryset'] = Ciudad.objects.none()
            else:
                # Creación: VACÍO TOTAL
                kwargs['queryset'] = Ciudad.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    class Media:
            js = ('servicios/js/paquete_filtros.js',)