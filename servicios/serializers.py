from rest_framework import serializers
from django.core.mail import EmailMultiAlternatives
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Mensaje
from email.mime.image import MIMEImage
import os
from django.conf import settings


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
            # Versión texto plano (respaldo)
            mensaje_texto = f"""
NUEVO CONTACTO:

NOMBRE: {cliente.nombre_completo}
EMAIL: {cliente.email}
TELÉFONO: {cliente.telefono}

MENSAJE:
{solicitud.mensaje}
"""
            
            # Versión HTML con logo usando CID (Content-ID)
            mensaje_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        
        <!-- Header con logo -->
        <div style="background-color: #B8860B; padding: 20px; text-align: center;">
            <img src="cid:logo_corpodg" alt="CORPODG Logo" style="max-width: 200px; height: auto; margin-bottom: 10px;" />
            <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 14px;">Nuevo contacto desde la web</p>
        </div>
        
        <!-- Contenido -->
        <div style="padding: 30px;">
            <h2 style="color: #333; border-bottom: 2px solid #B8860B; padding-bottom: 10px;">Datos del Cliente</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; background-color: #f9f9f9; font-weight: bold; width: 30%;">Nombre:</td>
                    <td style="padding: 10px; background-color: #f9f9f9;">{cliente.nombre_completo}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Email:</td>
                    <td style="padding: 10px;"><a href="mailto:{cliente.email}" style="color: #B8860B;">{cliente.email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 10px; background-color: #f9f9f9; font-weight: bold;">Teléfono:</td>
                    <td style="padding: 10px; background-color: #f9f9f9;"><a href="tel:{cliente.telefono}" style="color: #B8860B;">{cliente.telefono}</a></td>
                </tr>
            </table>
            
            <h2 style="color: #333; border-bottom: 2px solid #B8860B; padding-bottom: 10px;">Mensaje</h2>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #B8860B;">
                <p style="margin: 0; line-height: 1.6; color: #555;">{solicitud.mensaje}</p>
            </div>
        </div>
        
        
        <div style="background-color: #333; padding: 20px; text-align: center;">
            <p style="color: #ffffff; margin: 0; font-size: 12px;">© 2026 CorpoDG - Todos los derechos reservados</p>
            <p style="color: #B8860B; margin: 10px 0 0 0; font-size: 11px;">Este correo fue generado automáticamente desde el formulario de contacto</p>
        </div>
        
    </div>
</body>
</html>
"""
            
            # Crear el correo con EmailMultiAlternatives para adjuntar la imagen
            email = EmailMultiAlternatives(
                subject='NUEVO CLIENTE LISTO PARA CONTACTO DESDE LA WEB',
                body=mensaje_texto,  
                from_email='no-reply@corpodg.com',
                to=['miltondaviladt@gmail.com']
            )
            
            # Adjuntar la versión HTML
            email.attach_alternative(mensaje_html, "text/html")
            
            # Adjuntar la imagen del logo como inline
            # Ruta de la imagen: servicios/static/logo.png
            logo_path = os.path.join(settings.BASE_DIR, 'servicios', 'static', 'logo.png')
            
            # Verificar si existe el archivo de logo
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as img:
                    logo_img = MIMEImage(img.read())
                    logo_img.add_header('Content-ID', '<logo_corpodg>')
                    logo_img.add_header('Content-Disposition', 'inline', filename='logo.png')
                    email.attach(logo_img)
            
            # Enviar el correo
            email.send(fail_silently=False)
            
        except Exception as e:
            print(f"Error enviando correo: {e}")
        
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
