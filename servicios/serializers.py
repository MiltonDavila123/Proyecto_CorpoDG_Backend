from rest_framework import serializers
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Region, PaisRegion, Ciudad, Aerolinea, PaqueteTuristico
from .notifications import enviar_whatsapp_contacto, enviar_correo_contacto


class SolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = ['id', 'mensaje', 'fecha_creacion', 'atendido']
        read_only_fields = ['fecha_creacion', 'atendido']


class ClienteSerializer(serializers.ModelSerializer):
    solicitudes = SolicitudSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = ['id', 'nombre_completo', 'email', 'telefono', 'fecha_registro', 'solicitudes']
        read_only_fields = ['fecha_registro']


class ContactoSerializer(serializers.Serializer):
    """
    Serializer para el formulario de contacto.
    Maneja la lógica de crear cliente si no existe y agregar la solicitud.
    """
    nombre_completo = serializers.CharField(max_length=50)
    email = serializers.EmailField(max_length=80)
    telefono = serializers.CharField(max_length=15)
    mensaje = serializers.CharField(max_length=500)

    def create(self, validated_data):
        mensaje = validated_data.pop('mensaje')
        
        # Buscar si el cliente ya existe por email
        cliente, created = Cliente.objects.get_or_create(
            email=validated_data['email'],
            defaults={
                'nombre_completo': validated_data['nombre_completo'],
                'telefono': validated_data['telefono']
            }
        )
        
        # Si el cliente ya existía, actualizamos sus datos
        if not created:
            cliente.nombre_completo = validated_data['nombre_completo']
            cliente.telefono = validated_data['telefono']
            cliente.save()
        
        # Crear la solicitud
        solicitud = Solicitud.objects.create(
            cliente=cliente,
            mensaje=mensaje
        )
        
        # Enviar correo a la empresa
        try:
            enviar_correo_contacto(
                cliente_nombre=cliente.nombre_completo,
                cliente_email=cliente.email,
                cliente_telefono=cliente.telefono,
                mensaje=solicitud.mensaje
            )
        except Exception as e:
            print(f"Error enviando correo: {e}")
        
        # Enviar notificación por WhatsApp
        try:
            enviar_whatsapp_contacto(
                cliente_nombre=cliente.nombre_completo,
                cliente_email=cliente.email,
                cliente_telefono=cliente.telefono,
                mensaje=mensaje
            )
        except Exception as e:
            print(f"Error enviando WhatsApp: {e}")
        
        return {
            'cliente': cliente,
            'solicitud': solicitud,
            'cliente_nuevo': created
        }


class DestinoSerializer(serializers.ModelSerializer):
    """Serializer para destinos turísticos"""
    class Meta:
        model = Destino
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class HotelSerializer(serializers.ModelSerializer):
    """Serializer para hoteles"""
    destino_nombre = serializers.CharField(source='destino.nombre', read_only=True)
    servicios_lista = serializers.SerializerMethodField()
    
    class Meta:
        model = Hotel
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_servicios_lista(self, obj):
        return [s.strip() for s in obj.servicios.split(',') if s.strip()]


class VueloSerializer(serializers.ModelSerializer):
    """Serializer para vuelos"""
    aerolinea_nombre = serializers.CharField(source='aerolinea.nombre', read_only=True)
    aerolinea_logo = serializers.URLField(source='aerolinea.logo_url', read_only=True)
    origen_nombre = serializers.CharField(source='origen.nombre', read_only=True)
    origen_pais = serializers.CharField(source='origen.pais.nombre', read_only=True)
    destino_nombre = serializers.CharField(source='destino.nombre', read_only=True)
    destino_pais = serializers.CharField(source='destino.pais.nombre', read_only=True)
    
    class Meta:
        model = Vuelo
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class RentaAutoSerializer(serializers.ModelSerializer):
    """Serializer para renta de autos"""
    caracteristicas_lista = serializers.SerializerMethodField()
    ciudad_nombre = serializers.CharField(source='ciudad.nombre', read_only=True)
    ciudad_pais = serializers.CharField(source='ciudad.pais.nombre', read_only=True)
    
    class Meta:
        model = RentaAuto
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_caracteristicas_lista(self, obj):
        return [c.strip() for c in obj.caracteristicas.split(',') if c.strip()]


# =====================================================
# SERIALIZERS PARA PAQUETES TURÍSTICOS
# =====================================================

class CiudadSerializer(serializers.ModelSerializer):
    """Serializer para ciudades"""
    pais_nombre = serializers.CharField(source='pais.nombre', read_only=True)
    region_nombre = serializers.CharField(source='pais.region.get_nombre_display', read_only=True)
    ubicacion_completa = serializers.ReadOnlyField()
    
    class Meta:
        model = Ciudad
        fields = ['id', 'nombre', 'codigo_aeropuerto', 'es_capital', 'imagen_url', 'pais', 'pais_nombre', 'region_nombre', 'ubicacion_completa', 'activo']


class PaisRegionSerializer(serializers.ModelSerializer):
    """Serializer para países/destinos de cada región"""
    region_nombre = serializers.CharField(source='region.get_nombre_display', read_only=True)
    ciudades = CiudadSerializer(many=True, read_only=True)
    cantidad_ciudades = serializers.SerializerMethodField()
    
    class Meta:
        model = PaisRegion
        fields = ['id', 'nombre', 'codigo_pais', 'bandera_url', 'region', 'region_nombre', 'ciudades', 'cantidad_ciudades', 'activo']
    
    def get_cantidad_ciudades(self, obj):
        return obj.ciudades.filter(activo=True).count()


class PaisRegionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de países"""
    region_nombre = serializers.CharField(source='region.get_nombre_display', read_only=True)
    cantidad_ciudades = serializers.SerializerMethodField()
    
    class Meta:
        model = PaisRegion
        fields = ['id', 'nombre', 'codigo_pais', 'bandera_url', 'region', 'region_nombre', 'cantidad_ciudades', 'activo']
    
    def get_cantidad_ciudades(self, obj):
        return obj.ciudades.filter(activo=True).count()


class RegionSerializer(serializers.ModelSerializer):
    """Serializer para regiones"""
    nombre_display = serializers.CharField(source='get_nombre_display', read_only=True)
    paises = PaisRegionSerializer(many=True, read_only=True)
    cantidad_paquetes = serializers.SerializerMethodField()
    
    class Meta:
        model = Region
        fields = ['id', 'nombre', 'nombre_display', 'descripcion', 'imagen_url', 'activo', 'orden', 'paises', 'cantidad_paquetes']
    
    def get_cantidad_paquetes(self, obj):
        return obj.paquetes.filter(activo=True).count()


class RegionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de regiones"""
    nombre_display = serializers.CharField(source='get_nombre_display', read_only=True)
    cantidad_paises = serializers.SerializerMethodField()
    cantidad_paquetes = serializers.SerializerMethodField()
    
    class Meta:
        model = Region
        fields = ['id', 'nombre', 'nombre_display', 'imagen_url', 'activo', 'orden', 'cantidad_paises', 'cantidad_paquetes']
    
    def get_cantidad_paises(self, obj):
        return obj.paises.filter(activo=True).count()
    
    def get_cantidad_paquetes(self, obj):
        return obj.paquetes.filter(activo=True).count()


class AerolineaSerializer(serializers.ModelSerializer):
    """Serializer para aerolíneas"""
    class Meta:
        model = Aerolinea
        fields = ['id', 'nombre', 'logo_url', 'activo']


class PaqueteTuristicoListSerializer(serializers.ModelSerializer):
    """Serializer para listado de paquetes (Cards) - Incluye todos los campos"""
    region_nombre = serializers.CharField(source='region.get_nombre_display', read_only=True)
    pais_nombre = serializers.CharField(source='pais_destino.nombre', read_only=True)
    pais_bandera = serializers.URLField(source='pais_destino.bandera_url', read_only=True)
    ciudad_nombre = serializers.CharField(source='ciudad_destino.nombre', read_only=True, allow_null=True)
    aerolinea_nombre = serializers.CharField(source='aerolinea.nombre', read_only=True)
    aerolinea_logo = serializers.URLField(source='aerolinea.logo_url', read_only=True)
    texto_paquete = serializers.ReadOnlyField()
    destino_completo = serializers.ReadOnlyField()
    
    # Campos para los iconos de "Paquete incluye"
    paquete_incluye = serializers.SerializerMethodField()
    
    # Lugares destacados como lista
    lugares_destacados_lista = serializers.SerializerMethodField()
    
    # Labels legibles para choices
    tipo_paquete_display = serializers.CharField(source='get_tipo_paquete_display', read_only=True)
    temporada_display = serializers.CharField(source='get_temporada_display', read_only=True)
    tipo_viaje_display = serializers.CharField(source='get_tipo_viaje_display', read_only=True)
    
    class Meta:
        model = PaqueteTuristico
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_paquete_incluye(self, obj):
        return {
            'vuelo': obj.incluye_vuelo,
            'hotel': obj.incluye_hotel,
            'alimentacion': obj.incluye_alimentacion,
            'traslados': obj.incluye_traslados,
            'tours': obj.incluye_tours,
            'seguro': obj.incluye_seguro,
        }
    
    def get_lugares_destacados_lista(self, obj):
        if obj.lugares_destacados:
            return [l.strip() for l in obj.lugares_destacados.split(',') if l.strip()]
        return []


class PaqueteTuristicoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de paquete"""
    region_nombre = serializers.CharField(source='region.get_nombre_display', read_only=True)
    pais_nombre = serializers.CharField(source='pais_destino.nombre', read_only=True)
    pais_bandera = serializers.URLField(source='pais_destino.bandera_url', read_only=True)
    ciudad_nombre = serializers.CharField(source='ciudad_destino.nombre', read_only=True, allow_null=True)
    aerolinea_nombre = serializers.CharField(source='aerolinea.nombre', read_only=True)
    aerolinea_logo = serializers.URLField(source='aerolinea.logo_url', read_only=True)
    texto_paquete = serializers.ReadOnlyField()
    destino_completo = serializers.ReadOnlyField()
    
    # Campos para los iconos de "Paquete incluye"
    paquete_incluye = serializers.SerializerMethodField()
    
    # Lugares destacados como lista
    lugares_destacados_lista = serializers.SerializerMethodField()
    
    # Labels legibles para choices
    tipo_paquete_display = serializers.CharField(source='get_tipo_paquete_display', read_only=True)
    temporada_display = serializers.CharField(source='get_temporada_display', read_only=True)
    tipo_viaje_display = serializers.CharField(source='get_tipo_viaje_display', read_only=True)
    
    class Meta:
        model = PaqueteTuristico
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_paquete_incluye(self, obj):
        return {
            'vuelo': obj.incluye_vuelo,
            'hotel': obj.incluye_hotel,
            'alimentacion': obj.incluye_alimentacion,
            'traslados': obj.incluye_traslados,
            'tours': obj.incluye_tours,
            'seguro': obj.incluye_seguro,
        }
    
    def get_lugares_destacados_lista(self, obj):
        if obj.lugares_destacados:
            return [l.strip() for l in obj.lugares_destacados.split(',') if l.strip()]
        return []
