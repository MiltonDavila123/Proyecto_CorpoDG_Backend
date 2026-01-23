from rest_framework import serializers
from django.core.mail import send_mail
from .models import Cliente, Solicitud


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
            send_mail(
                subject='NUEVO CLIENTE LISTO PARA CONTACTO DESDE LA WEB ',
                message=f"""
NUEVO CONTACTO:

NOMBRE: {cliente.nombre_completo}
EMAIL: {cliente.email}
TELÉFONO: {cliente.telefono}

MENSAJE:
{solicitud.mensaje}
""",
                from_email='no-reply@corpodg.com',
                recipient_list=['milton.davila.torres@udla.edu.ec'],  # Cambia por el correo de la empresa
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando correo: {e}")
        
        return {
            'cliente': cliente,
            'solicitud': solicitud,
            'cliente_nuevo': created
        }
