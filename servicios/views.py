from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Mensaje
from .serializers import (
    ClienteSerializer, SolicitudSerializer, ContactoSerializer,
    DestinoSerializer, HotelSerializer, VueloSerializer,
    RentaAutoSerializer, MensajeSerializer
)


class ClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para ver y editar clientes"""
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class SolicitudViewSet(viewsets.ModelViewSet):
    """ViewSet para ver y editar solicitudes"""
    queryset = Solicitud.objects.all()
    serializer_class = SolicitudSerializer


@api_view(['POST'])
def contacto(request):
    """
    Endpoint para el formulario de contacto.
    Si el cliente (por email) ya existe, solo agrega una nueva solicitud.
    Si no existe, crea el cliente y la solicitud.
    """
    serializer = ContactoSerializer(data=request.data)
    
    if serializer.is_valid():
        result = serializer.save()
        
        response_data = {
            'success': True,
            'message': 'Solicitud recibida correctamente',
            'cliente': {
                'id': result['cliente'].id,
                'nombre_completo': result['cliente'].nombre_completo,
                'email': result['cliente'].email,
                'es_nuevo': result['cliente_nuevo']
            },
            'solicitud_id': result['solicitud'].id
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class DestinoViewSet(viewsets.ModelViewSet):
    """ViewSet para destinos turísticos"""
    queryset = Destino.objects.filter(activo=True)
    serializer_class = DestinoSerializer


class HotelViewSet(viewsets.ModelViewSet):
    """ViewSet para hoteles"""
    queryset = Hotel.objects.filter(disponible=True)
    serializer_class = HotelSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        destino_id = self.request.query_params.get('destino', None)
        if destino_id:
            queryset = queryset.filter(destino_id=destino_id)
        return queryset


class VueloViewSet(viewsets.ModelViewSet):
    """ViewSet para vuelos"""
    queryset = Vuelo.objects.filter(disponible=True)
    serializer_class = VueloSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        origen = self.request.query_params.get('origen', None)
        destino = self.request.query_params.get('destino', None)
        if origen:
            queryset = queryset.filter(origen__icontains=origen)
        if destino:
            queryset = queryset.filter(destino__icontains=destino)
        return queryset


class RentaAutoViewSet(viewsets.ModelViewSet):
    """ViewSet para renta de autos"""
    queryset = RentaAuto.objects.filter(disponible=True)
    serializer_class = RentaAutoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        tipo = self.request.query_params.get('tipo', None)
        ubicacion = self.request.query_params.get('ubicacion', None)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if ubicacion:
            queryset = queryset.filter(ubicacion__icontains=ubicacion)
        return queryset


class MensajeViewSet(viewsets.ModelViewSet):
    """ViewSet para mensajes de contacto"""
    queryset = Mensaje.objects.all()
    serializer_class = MensajeSerializer
