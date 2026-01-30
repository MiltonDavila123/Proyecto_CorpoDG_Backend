from rest_framework import serializers
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Mensaje
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
    class Meta:
        model = Vuelo
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class RentaAutoSerializer(serializers.ModelSerializer):
    """Serializer para renta de autos"""
    caracteristicas_lista = serializers.SerializerMethodField()
    
    class Meta:
        model = RentaAuto
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_caracteristicas_lista(self, obj):
        return [c.strip() for c in obj.caracteristicas.split(',') if c.strip()]


class MensajeSerializer(serializers.ModelSerializer):
    """Serializer para mensajes de contacto"""
    class Meta:
        model = Mensaje
        fields = '__all__'
        read_only_fields = ['fecha_envio', 'leido', 'respondido']
