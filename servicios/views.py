from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .models import Cliente, Solicitud, Destino, Hotel, Vuelo, RentaAuto, Region, PaisRegion, Ciudad, Aerolinea, PaqueteTuristico
from .serializers import (
    ClienteSerializer, SolicitudSerializer, ContactoSerializer,
    DestinoSerializer, HotelSerializer, VueloSerializer,
    RentaAutoSerializer, RegionSerializer, RegionListSerializer,
    PaisRegionSerializer, PaisRegionListSerializer, CiudadSerializer, AerolineaSerializer,
    PaqueteTuristicoListSerializer, PaqueteTuristicoDetailSerializer
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
        ciudad_id = self.request.query_params.get('ciudad', None)
        pais_id = self.request.query_params.get('pais', None)
        region_id = self.request.query_params.get('region', None)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if ubicacion:
            queryset = queryset.filter(ubicacion__icontains=ubicacion)
        if ciudad_id:
            queryset = queryset.filter(ciudad_id=ciudad_id)
        if pais_id:
            queryset = queryset.filter(ciudad__pais_id=pais_id)
        if region_id:
            queryset = queryset.filter(ciudad__pais__region_id=region_id)
        return queryset


# =====================================================
# VIEWSETS PARA PAQUETES TURÍSTICOS
# =====================================================

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para regiones (solo lectura)"""
    queryset = Region.objects.filter(activo=True)
    serializer_class = RegionSerializer  # Siempre incluir países y ciudades
    
    @action(detail=True, methods=['get'])
    def paises(self, request, pk=None):
        """Obtener países de una región específica"""
        region = self.get_object()
        paises = region.paises.filter(activo=True)
        serializer = PaisRegionListSerializer(paises, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def paquetes(self, request, pk=None):
        """Obtener paquetes de una región específica"""
        region = self.get_object()
        paquetes = region.paquetes.filter(activo=True)
        serializer = PaqueteTuristicoListSerializer(paquetes, many=True)
        return Response(serializer.data)


class PaisRegionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para países/destinos de regiones (solo lectura)"""
    queryset = PaisRegion.objects.filter(activo=True)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaisRegionSerializer
        return PaisRegionListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        region_id = self.request.query_params.get('region', None)
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        return queryset
    
    @action(detail=True, methods=['get'])
    def ciudades(self, request, pk=None):
        """Obtener ciudades de un país específico"""
        pais = self.get_object()
        ciudades = pais.ciudades.filter(activo=True)
        serializer = CiudadSerializer(ciudades, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def paquetes(self, request, pk=None):
        """Obtener paquetes de un país específico"""
        pais = self.get_object()
        paquetes = pais.paquetes.filter(activo=True)
        serializer = PaqueteTuristicoListSerializer(paquetes, many=True)
        return Response(serializer.data)


class CiudadViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para ciudades (solo lectura)"""
    queryset = Ciudad.objects.filter(activo=True)
    serializer_class = CiudadSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        pais_id = self.request.query_params.get('pais', None)
        region_id = self.request.query_params.get('region', None)
        es_capital = self.request.query_params.get('capital', None)
        
        if pais_id:
            queryset = queryset.filter(pais_id=pais_id)
        if region_id:
            queryset = queryset.filter(pais__region_id=region_id)
        if es_capital and es_capital.lower() == 'true':
            queryset = queryset.filter(es_capital=True)
        return queryset


class AerolineaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para aerolíneas (solo lectura)"""
    queryset = Aerolinea.objects.filter(activo=True)
    serializer_class = AerolineaSerializer
    
    @action(detail=True, methods=['get'])
    def vuelos(self, request, pk=None):
        """Obtener vuelos de una aerolínea específica"""
        aerolinea = self.get_object()
        vuelos = aerolinea.vuelos.filter(disponible=True)
        serializer = VueloSerializer(vuelos, many=True)
        return Response(serializer.data)


class PaqueteTuristicoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para paquetes turísticos (solo lectura)"""
    queryset = PaqueteTuristico.objects.filter(activo=True)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaqueteTuristicoDetailSerializer
        return PaqueteTuristicoListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por región
        region_id = self.request.query_params.get('region', None)
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        # Filtrar por país
        pais_id = self.request.query_params.get('pais', None)
        if pais_id:
            queryset = queryset.filter(pais_destino_id=pais_id)
        
        # Filtrar por tipo de paquete
        tipo = self.request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo_paquete=tipo)
        
        # Filtrar por temporada
        temporada = self.request.query_params.get('temporada', None)
        if temporada:
            queryset = queryset.filter(temporada=temporada)
        
        # Filtrar por precio máximo
        precio_max = self.request.query_params.get('precio_max', None)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
        
        # Filtrar por destacados
        destacados = self.request.query_params.get('destacados', None)
        if destacados and destacados.lower() == 'true':
            queryset = queryset.filter(destacado=True)
        
        # Filtrar por aerolínea
        aerolinea_id = self.request.query_params.get('aerolinea', None)
        if aerolinea_id:
            queryset = queryset.filter(aerolinea_id=aerolinea_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def destacados(self, request):
        """Obtener solo paquetes destacados"""
        paquetes = self.get_queryset().filter(destacado=True)
        serializer = PaqueteTuristicoListSerializer(paquetes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_region(self, request):
        """Obtener paquetes agrupados por región"""
        regiones = Region.objects.filter(activo=True)
        resultado = []
        
        for region in regiones:
            paquetes = region.paquetes.filter(activo=True)[:6]  # Máximo 6 por región
            if paquetes.exists():
                resultado.append({
                    'region': RegionListSerializer(region).data,
                    'paquetes': PaqueteTuristicoListSerializer(paquetes, many=True).data
                })
        
        return Response(resultado)


# =====================================================
# ENDPOINTS AJAX PARA ADMIN
# =====================================================

from django.http import JsonResponse

def paises_por_region(request, region_id):
    """Devuelve los países de una región específica para el admin"""
    paises = PaisRegion.objects.filter(region_id=region_id, activo=True).values('id', 'nombre')
    return JsonResponse(list(paises), safe=False)

def ciudades_por_pais(request, pais_id):
    """Devuelve las ciudades de un país específico para el admin"""
    ciudades = Ciudad.objects.filter(pais_id=pais_id, activo=True).values('id', 'nombre')
    return JsonResponse(list(ciudades), safe=False)
