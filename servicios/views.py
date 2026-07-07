from rest_framework import viewsets, status
from django.db.models import Count, Q
from rest_framework.views import APIView
from .searchFlights import buscar_vuelos_sabre
from .revalidateFlight import revalidar_itinerario
from .seatMapFlight import obtener_mapa_asientos
from .bookingFlight import crear_checkout, confirmar_reserva, obtener_reserva_guardada
from .bookingPaquete import (
    crear_checkout_paquete, confirmar_reserva_paquete,
    obtener_reserva_paquete_guardada,
)
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Cliente, Solicitud, Destino, Vuelo, Region, PaisRegion, Ciudad, Aerolinea, Aeropuerto, PaqueteTuristico, ConfiguracionDestacados, OrdenVueloDestacado, OrdenPaqueteDestacado, OrdenDestinoDestacado, TipoPaquete, Temporada
from .serializers import (
    ClienteSerializer, SolicitudSerializer, ContactoSerializer,
    DestinoSerializer, VueloSerializer,
    RegionSerializer, RegionListSerializer,
    PaisRegionSerializer, PaisRegionListSerializer, CiudadSerializer, AerolineaSerializer,
    AeropuertoSerializer, AeropuertoListSerializer, AeropuertoAutocompleteSerializer,
    PaqueteTuristicoListSerializer, PaqueteTuristicoDetailSerializer,
    TipoPaqueteSerializer, TemporadaSerializer
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

    def get_queryset(self):
        queryset = super().get_queryset()
        pais_id = self.request.query_params.get('pais', None)
        ciudad_id = self.request.query_params.get('ciudad', None)
        destacado = self.request.query_params.get('destacado', None)
        
        if pais_id:
            queryset = queryset.filter(pais_id=pais_id)
        if ciudad_id:
            queryset = queryset.filter(ciudad_id=ciudad_id)
        if destacado:
            queryset = queryset.filter(destacado=destacado.lower() in ['true', '1', 't', 'yes'])
            
        return queryset

    @action(detail=False, methods=['get'])
    def destacados(self, request):
        """Obtener destinos destacados (ordenados según admin general y limitados)"""
        config = ConfiguracionDestacados.load()
        
        ordenados_qs = OrdenDestinoDestacado.objects.filter(
            configuracion=config,
            destino__activo=True,
            destino__destacado=True
        ).select_related('destino')
        
        ordenados = []
        ordered_ids = []
        for orden in ordenados_qs:
            ordenados.append(orden.destino)
            ordered_ids.append(orden.destino.id)
            
        restantes = self.queryset.filter(destacado=True).exclude(id__in=ordered_ids).order_by('-fecha_creacion')
        
        resultado_final = (ordenados + list(restantes))[:config.limite_destinos]
        
        serializer = self.get_serializer(resultado_final, many=True)
        return Response(serializer.data)


class VueloViewSet(viewsets.ModelViewSet):
    """ViewSet para vuelos"""
    queryset = Vuelo.objects.filter(disponible=True)
    serializer_class = VueloSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        origen = self.request.query_params.get('origen', None)
        destino = self.request.query_params.get('destino', None)
        if origen:
            queryset = queryset.filter(
                Q(origen__nombre__icontains=origen) | 
                Q(origen__ciudad__nombre__icontains=origen) |
                Q(origen__codigo_iata__icontains=origen)
            )
        if destino:
            queryset = queryset.filter(
                Q(destino__nombre__icontains=destino) |
                Q(destino__ciudad__nombre__icontains=destino) |
                Q(destino__codigo_iata__icontains=destino)
            )
        return queryset

    @action(detail=False, methods=['get'])
    def destacados(self, request):
        """Obtener vuelos destacados (ordenados según admin general y limitados)"""
        config = ConfiguracionDestacados.load()
        
        ordenados_qs = OrdenVueloDestacado.objects.filter(
            configuracion=config,
            vuelo__disponible=True,
            vuelo__destacado=True
        ).select_related('vuelo')
        
        ordenados = []
        ordered_ids = []
        for orden in ordenados_qs:
            ordenados.append(orden.vuelo)
            ordered_ids.append(orden.vuelo.id)
            
        restantes = self.queryset.filter(destacado=True).exclude(id__in=ordered_ids).order_by('-fecha_creacion')
        
        resultado_final = (ordenados + list(restantes))[:config.limite_vuelos]
        
        serializer = self.get_serializer(resultado_final, many=True)
        return Response(serializer.data)


# =====================================================
# VIEWSETS PARA PAQUETES TURÍSTICOS
# =====================================================

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para regiones (solo lectura)"""
    
    # 1. OPTIMIZACIÓN DE CONSULTA (SQL):
    # Usamos annotate para que la base de datos cuente los países y paquetes.
    # Esto evita traer los objetos a memoria.
    queryset = Region.objects.annotate(
        total_paises=Count('paises', distinct=True),
        total_paquetes=Count('paquetes', distinct=True)
    ).filter(activo=True).order_by('orden')
    
    # 2. SELECCIÓN DINÁMICA DE SERIALIZER:
    def get_serializer_class(self):
        # Si la petición es para ver la lista (api/regiones/), usa el ligero
        if self.action == 'list':
            return RegionListSerializer
        # Si es para ver un detalle (api/regiones/1/), usa el pesado
        return RegionSerializer

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
        PaqueteTuristico.sincronizar_vigencia()
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
        PaqueteTuristico.sincronizar_vigencia()
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
    
    def get_queryset(self):
        queryset = super().get_queryset()
        pais = self.request.query_params.get('pais', None)
        search = self.request.query_params.get('search', None)
        
        if pais:
            queryset = queryset.filter(pais_origen__icontains=pais)
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo_iata__icontains=search) |
                Q(codigo_icao__icontains=search)
            )
        return queryset
    
    @action(detail=True, methods=['get'])
    def vuelos(self, request, pk=None):
        """Obtener vuelos de una aerolínea específica"""
        aerolinea = self.get_object()
        vuelos = aerolinea.vuelos.filter(disponible=True)
        serializer = VueloSerializer(vuelos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def buscar_iata(self, request):
        """
        Buscar aerolínea por código IATA exacto.
        Uso: GET /api/aerolineas/buscar_iata/?codigo=AV
        """
        codigo = request.query_params.get('codigo', '').strip().upper()
        
        if not codigo:
            return Response({'error': 'Parámetro "codigo" requerido'}, status=400)
        
        try:
            aerolinea = Aerolinea.objects.get(codigo_iata=codigo, activo=True)
            serializer = AerolineaSerializer(aerolinea)
            return Response(serializer.data)
        except Aerolinea.DoesNotExist:
            return Response({'error': f'Aerolínea con código IATA "{codigo}" no encontrada'}, status=404)


class AeropuertoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para aeropuertos (solo lectura)"""
    queryset = Aeropuerto.objects.filter(activo=True)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AeropuertoListSerializer
        return AeropuertoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        pais_id = self.request.query_params.get('pais', None)
        region = self.request.query_params.get('region', None)
        ciudad_id = self.request.query_params.get('ciudad', None)
        search = self.request.query_params.get('search', None)
        
        if pais_id:
            queryset = queryset.filter(pais_id=pais_id)
        if region:
            queryset = queryset.filter(region__iexact=region)
        if ciudad_id:
            queryset = queryset.filter(ciudad_id=ciudad_id)
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo_iata__icontains=search) |
                Q(codigo_icao__icontains=search) |
                Q(nombre_ciudad__icontains=search)
            )
        return queryset
    
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """
        Endpoint optimizado para autocompletado de aeropuertos.
        Busca por código IATA, ICAO, nombre, ciudad o país.
        Devuelve máximo 10 resultados.
        
        Uso: GET /api/aeropuertos/autocomplete/?q=bogota
        """
        q = request.query_params.get('q', '').strip()
        
        if len(q) < 2:
            return Response({
                'results': [],
                'message': 'Ingresa al menos 2 caracteres para buscar'
            })
        
        # Búsqueda optimizada en múltiples campos
        aeropuertos = Aeropuerto.objects.filter(
            activo=True
        ).filter(
            Q(codigo_iata__icontains=q) |
            Q(codigo_icao__icontains=q) |
            Q(nombre__icontains=q) |
            Q(nombre_ciudad__icontains=q) |
            Q(ciudad__nombre__icontains=q) |
            Q(pais__nombre__icontains=q)
        ).select_related('ciudad', 'pais')[:10]  # Limita a 10 resultados
        
        serializer = AeropuertoAutocompleteSerializer(aeropuertos, many=True)
        
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })


class TipoPaqueteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para tipos de paquete (solo lectura)"""
    queryset = TipoPaquete.objects.filter(activo=True)
    serializer_class = TipoPaqueteSerializer


class TemporadaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para temporadas (solo lectura)"""
    queryset = Temporada.objects.filter(activo=True)
    serializer_class = TemporadaSerializer


class PaqueteTuristicoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para paquetes turísticos (solo lectura)"""
    queryset = PaqueteTuristico.objects.filter(activo=True)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaqueteTuristicoDetailSerializer
        return PaqueteTuristicoListSerializer
    
    def get_queryset(self):
        # Sincronizar el estado según la fecha de vigencia (desactiva vencidos, reactiva vigentes)
        PaqueteTuristico.sincronizar_vigencia()

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
            queryset = queryset.filter(tipo_paquete__nombre__iexact=tipo)
        
        # Filtrar por temporada
        temporada = self.request.query_params.get('temporada', None)
        if temporada:
            queryset = queryset.filter(temporada__nombre__iexact=temporada)
        
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
        """Obtener paquetes destacados (ordenados según admin general y limitados)"""
        # Sincronizar el estado según la fecha de vigencia (desactiva vencidos, reactiva vigentes)
        PaqueteTuristico.sincronizar_vigencia()

        config = ConfiguracionDestacados.load()
        
        ordenados_qs = OrdenPaqueteDestacado.objects.filter(
            configuracion=config,
            paquete__activo=True,
            paquete__destacado=True
        ).select_related('paquete')
        
        ordenados = []
        ordered_ids = []
        for orden in ordenados_qs:
            ordenados.append(orden.paquete)
            ordered_ids.append(orden.paquete.id)
            
        restantes = self.get_queryset().filter(destacado=True).exclude(id__in=ordered_ids).order_by('-fecha_creacion')
        
        resultado_final = (ordenados + list(restantes))[:config.limite_paquetes]
        
        serializer = PaqueteTuristicoListSerializer(resultado_final, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_region(self, request):
        """Obtener paquetes agrupados por región"""
        # Sincronizar el estado según la fecha de vigencia (desactiva vencidos, reactiva vigentes)
        PaqueteTuristico.sincronizar_vigencia()

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
    
class BuscadorVuelosSabreView(APIView):
    """
    Endpoint para buscar vuelos en tiempo real usando Sabre BFM.
    Llama a tu archivo searchFlights.py
    """
    def post(self, request):
        # Datos que vienen del frontend
        data = request.data
        
        # Validaciones mínimas
        if not data.get('origin') or not data.get('destination') or not data.get('date'):
            return Response(
                {"error": "Faltan datos obligatorios (origin, destination, date)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Llamada a tu archivo searchFlights.py
        resultados = buscar_vuelos_sabre(data)

        # Manejo de errores
        if isinstance(resultados, dict) and "error" in resultados:
            codigo = resultados.get("code", 500)
            return Response(resultados, status=codigo)

        return Response(resultados, status=status.HTTP_200_OK)


class RevalidarVueloView(APIView):
    """Confirma si un itinerario sigue disponible para reservar.

    Body esperado:
    {
        "adults": 1, "children": 0, "infants": 0,
        "tramos": [
            {
                "fecha_salida": "YYYY-MM-DD",
                "segmentos": [
                    {
                        "numero_vuelo": 833,
                        "clase_servicio": "V",
                        "origen": "EWR", "destino": "MIA",
                        "fecha_hora_salida": "2026-05-31T12:20:00",
                        "fecha_hora_llegada": "2026-05-31T15:26:00",
                        "aerolinea_marketing": "AA",
                        "aerolinea_operadora": "AA"
                    }
                ]
            }
        ]
    }

    Tambien acepta directamente el objeto "opcion" devuelto por la busqueda
    (usa los subcampos salida/llegada/aerolinea/vuelo).
    """

    def post(self, request):
        data = request.data or {}
        if not data.get("tramos"):
            return Response(
                {"disponible": False, "error": "Faltan los tramos del itinerario"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultado = revalidar_itinerario(data)
        codigo = resultado.pop("code", None)
        if resultado.get("disponible"):
            return Response(resultado, status=status.HTTP_200_OK)
        return Response(resultado, status=codigo or status.HTTP_409_CONFLICT)


class SeatMapView(APIView):
    """Devuelve el mapa de asientos de un itinerario via Sabre Get Seats.

    Body esperado:
    {
      "opcion": { ... },               // la opcion completa devuelta por la busqueda
      "pasajeros": [
        {"passengerType":"ADT", "givenName":"JUAN", "surname":"PEREZ"}
      ],
      "moneda": "USD"                  // opcional
    }
    """

    def post(self, request):
        data = request.data or {}
        if not (data.get("opcion") or {}).get("tramos"):
            return Response(
                {"error": "Falta 'opcion' con sus 'tramos'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        resultado = obtener_mapa_asientos(data)
        codigo = resultado.pop("code", None)
        if codigo and codigo != 200:
            return Response(resultado, status=codigo)
        return Response(resultado, status=status.HTTP_200_OK)


# =====================================================
# BOOKING (Stripe Checkout + Sabre createBooking)
# =====================================================
class BookingCheckoutView(APIView):
    """Crea una sesion de Stripe Checkout y guarda el intent de reserva.

    Body:
    {
      "opcion": {...},
      "pasajeros": [...],
      "contacto": {"email": "...", "phone": "..."},
      "asientos_seleccionados": [...],   // opcional
      "moneda": "USD",                   // opcional
      "success_url": "...",              // opcional
      "cancel_url":  "..."
    }
    Devuelve: { checkout_url, session_id, booking_ref, monto, moneda }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        resultado = crear_checkout(data)
        codigo = resultado.pop("code", None) if "error" in resultado else None
        if codigo:
            return Response(resultado, status=codigo)
        return Response(resultado, status=status.HTTP_200_OK)


class BookingConfirmView(APIView):
    """Confirma la reserva tras un pago Stripe exitoso.

    Body: { "session_id": "cs_test_..." }
    Devuelve la reserva tipo Sabre createBookingResponse + 'resumen'.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        session_id = (request.data or {}).get("session_id")
        resultado = confirmar_reserva(session_id)
        codigo = resultado.pop("code", None) if "error" in resultado else None
        if codigo:
            return Response(resultado, status=codigo)
        return Response(resultado, status=status.HTTP_200_OK)


class StripeWebhookView(APIView):
    """Endpoint opcional para eventos Stripe (checkout.session.completed)."""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            import stripe
            from django.conf import settings as _s
            payload = request.body
            sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
            secret = getattr(_s, "STRIPE_WEBHOOK_SECRET", "")
            if secret and sig:
                event = stripe.Webhook.construct_event(payload, sig, secret)
            else:
                import json as _json
                event = _json.loads(payload.decode("utf-8"))
            return Response({"received": True, "type": event.get("type")},
                            status=status.HTTP_200_OK)
        except Exception as e:  # noqa: BLE001
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookingVoucherView(APIView):
    """Vista imprimible / PDF del voucher (boletos de vuelo) de una reserva.

    GET  /api/booking/voucher/?session_id=cs_test_...&format=pdf
    GET  /api/booking/voucher/?pnr=ABCDEF&format=html&doc=boletos
    POST /api/booking/voucher/   body: { reserva: {...}, format: "pdf"|"html", doc: "voucher"|"boletos" }
         (renderiza directamente la reserva enviada por el frontend,
          útil si la cache del backend ya expiró)

    format:
      - 'html' (default) -> documento HTML listo para imprimir (window.print()).
      - 'pdf'            -> archivo PDF descargable.
    doc:
      - 'voucher' (default) -> comprobante CorpoDG (itinerario + factura).
      - 'boletos'           -> boletos estilo aerolínea (PDF aparte).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        clave = (request.query_params.get("session_id")
                 or request.query_params.get("pnr"))
        formato = (request.query_params.get("format") or "html").lower()
        doc = (request.query_params.get("doc") or "voucher").lower()

        if not clave:
            return Response({"error": "Falta 'session_id' o 'pnr'"},
                            status=status.HTTP_400_BAD_REQUEST)

        reserva = obtener_reserva_guardada(clave)
        if not reserva:
            return Response(
                {"error": "Reserva no encontrada o expirada. "
                          "Reenvía la reserva por POST para regenerar el documento."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return self._responder(reserva, formato, doc)

    def post(self, request):
        data = request.data or {}
        reserva = data.get("reserva") or data
        formato = (data.get("format") or request.query_params.get("format")
                   or "html").lower()
        doc = (data.get("doc") or request.query_params.get("doc")
               or "voucher").lower()
        if not reserva or "booking" not in reserva:
            return Response({"error": "Falta 'reserva' (createBookingResponse)"},
                            status=status.HTTP_400_BAD_REQUEST)
        return self._responder(reserva, formato, doc)

    def _responder(self, reserva, formato, doc="voucher"):
        from django.http import HttpResponse
        from .bookingDocs import (
            render_voucher_html, generar_voucher_pdf,
            render_boletos_html, generar_boletos_pdf,
        )

        pnr = reserva.get("confirmationId") or "voucher"
        es_boletos = doc == "boletos"
        prefijo = "Boletos" if es_boletos else "CorpoDG"

        if formato == "pdf":
            pdf_bytes = (generar_boletos_pdf(reserva) if es_boletos
                         else generar_voucher_pdf(reserva))
            if not pdf_bytes:
                return Response(
                    {"error": "No se pudo generar el PDF (xhtml2pdf no disponible)"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            resp = HttpResponse(pdf_bytes, content_type="application/pdf")
            resp["Content-Disposition"] = f'inline; filename="{prefijo}_{pnr}.pdf"'
            return resp

        html = (render_boletos_html(reserva, modo="web") if es_boletos
                else render_voucher_html(reserva, modo="web"))
        return HttpResponse(html, content_type="text/html; charset=utf-8")



# =====================================================
# BOOKING DE PAQUETES (Stripe Checkout + voucher)
# =====================================================
class PaqueteCheckoutView(APIView):
    """Crea una sesión de Stripe Checkout para reservar un paquete.

    Body:
    {
      "paquete_id": 12,
      "n_personas": 2,
      "contacto": {"email": "...", "phone": "..."},
      "viajeros": [{"nombre": "...", "apellido": "...", "documento": "..."}],
      "fecha_viaje": "2026-08-15",   // opcional
      "moneda": "USD",               // opcional
      "success_url": "...",          // opcional
      "cancel_url":  "..."           // opcional
    }
    Devuelve: { checkout_url, session_id, paquete_id, monto, moneda, n_personas }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        resultado = crear_checkout_paquete(data)
        codigo = resultado.pop("code", None) if "error" in resultado else None
        if codigo:
            return Response(resultado, status=codigo)
        return Response(resultado, status=status.HTTP_200_OK)


class PaqueteConfirmView(APIView):
    """Confirma la reserva de un paquete tras un pago Stripe exitoso.

    Body: { "session_id": "cs_test_..." }
    Devuelve la reserva normalizada del paquete + 'pago'.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        session_id = (request.data or {}).get("session_id")
        resultado = confirmar_reserva_paquete(session_id)
        codigo = resultado.pop("code", None) if "error" in resultado else None
        if codigo:
            return Response(resultado, status=codigo)
        return Response(resultado, status=status.HTTP_200_OK)


class PaqueteVoucherView(APIView):
    """Vista imprimible / PDF del voucher de un paquete.

    GET  /api/paquetes/booking/voucher/?session_id=cs_test_...&format=pdf
    GET  /api/paquetes/booking/voucher/?loc=CDGPK-XXXXXX&format=html
    POST /api/paquetes/booking/voucher/  body: { reserva: {...}, format: "pdf"|"html" }

    format: 'html' (default) | 'pdf'
    """
    permission_classes = [AllowAny]

    def get(self, request):
        clave = (request.query_params.get("session_id")
                 or request.query_params.get("loc")
                 or request.query_params.get("localizador"))
        formato = (request.query_params.get("format") or "html").lower()
        if not clave:
            return Response({"error": "Falta 'session_id' o 'loc'"},
                            status=status.HTTP_400_BAD_REQUEST)
        reserva = obtener_reserva_paquete_guardada(clave)
        if not reserva:
            return Response(
                {"error": "Reserva no encontrada o expirada. "
                          "Reenvía la reserva por POST para regenerar el documento."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return self._responder(reserva, formato)

    def post(self, request):
        data = request.data or {}
        reserva = data.get("reserva") or data
        formato = (data.get("format") or request.query_params.get("format")
                   or "html").lower()
        if not reserva or "paquete" not in reserva:
            return Response({"error": "Falta 'reserva' con 'paquete'"},
                            status=status.HTTP_400_BAD_REQUEST)
        return self._responder(reserva, formato)

    def _responder(self, reserva, formato):
        from django.http import HttpResponse
        from .paqueteDocs import (
            render_voucher_paquete_html, generar_voucher_paquete_pdf,
        )
        loc = reserva.get("localizador") or "voucher"

        if formato == "pdf":
            pdf_bytes = generar_voucher_paquete_pdf(reserva)
            if not pdf_bytes:
                return Response(
                    {"error": "No se pudo generar el PDF (xhtml2pdf no disponible)"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            resp = HttpResponse(pdf_bytes, content_type="application/pdf")
            resp["Content-Disposition"] = f'inline; filename="CorpoDG_Paquete_{loc}.pdf"'
            return resp

        html = render_voucher_paquete_html(reserva, modo="web")
        return HttpResponse(html, content_type="text/html; charset=utf-8")



# =====================================================
# ENDPOINTS AJAX PARA ADMIN
# =====================================================
from django.http import JsonResponse
from .models import PaisRegion, Ciudad

# Esta función busca los países
def paises_por_region(request, region_id):
    paises = PaisRegion.objects.filter(region_id=region_id, activo=True).values('id', 'nombre').order_by('nombre')
    return JsonResponse(list(paises), safe=False)

# Esta función busca las ciudades
def ciudades_por_pais(request, pais_id):
    ciudades = Ciudad.objects.filter(pais_id=pais_id, activo=True).values('id', 'nombre').order_by('nombre')
    return JsonResponse(list(ciudades), safe=False)

def aeropuertos_por_ciudad(request, ciudad_id):
    from .models import Aeropuerto, Ciudad
    try:
        ciudad = Ciudad.objects.get(pk=ciudad_id)
        # 1. Intentar buscar aeropuertos vinculados exactamente a esa ciudad
        aeropuertos = Aeropuerto.objects.filter(ciudad_id=ciudad_id, activo=True).values('id', 'nombre', 'codigo_iata').order_by('nombre')
        
        # 2. Si no hay aeropuertos para esa ciudad en específico, entonces traer los del país correspondiente
        if not aeropuertos.exists():
            aeropuertos = Aeropuerto.objects.filter(pais_id=ciudad.pais_id, activo=True).values('id', 'nombre', 'codigo_iata').order_by('nombre')
            
        return JsonResponse(list(aeropuertos), safe=False)
    except Ciudad.DoesNotExist:
        return JsonResponse([], safe=False)

def aeropuertos_por_pais(request, pais_id):
    from .models import Aeropuerto
    aeropuertos = Aeropuerto.objects.filter(pais_id=pais_id, activo=True).values('id', 'nombre', 'codigo_iata').order_by('nombre')
    return JsonResponse(list(aeropuertos), safe=False)


# =====================================================
# CHATBOT — Vista principal
# =====================================================

class ChatbotView(APIView):
    """
    Endpoint para el chatbot de CorpoDG.
    Recibe el mensaje del usuario y el historial de conversación,
    retorna la respuesta del asistente y el historial actualizado.

    POST /api/chatbot/
    Body: { "mensaje": str, "historial": list (opcional) }
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        mensaje = request.data.get('mensaje', '').strip()

        if not mensaje:
            return Response(
                {"error": "El campo 'mensaje' es requerido y no puede estar vacío."},
                status=status.HTTP_400_BAD_REQUEST
            )

        historial = request.data.get('historial', [])

        # Validar que historial sea una lista
        if not isinstance(historial, list):
            historial = []

        try:
            from .chatbot import procesar_mensaje
            resultado = procesar_mensaje(mensaje, historial)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error procesando el mensaje: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



def health_check(request):
    return JsonResponse({"status": "ok"})


from django.contrib.auth.models import User

SEED_SECRET = "corpodg-seed-2024"

def seed_database(request):
    if request.GET.get("secret") != SEED_SECRET:
        return JsonResponse({"error": "invalid secret"}, status=403)

    from .models import (
        Region, PaisRegion, Ciudad, Aerolinea, Aeropuerto,
        TipoPaquete, Temporada, TipoViaje, Destino,
        PaqueteTuristico, ConfiguracionDestacados
    )

    created = {}
    skipped = {}

    def safe_create(model, lookup, defaults):
        obj, was_created = model.objects.get_or_create(**lookup, defaults=defaults)
        if was_created:
            key = model.__name__
            created.setdefault(key, 0)
            created[key] += 1
        else:
            key = model.__name__
            skipped.setdefault(key, 0)
            skipped[key] += 1
        return obj

    # --- Admin ---
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@corpodg.ec", "Admin123!")
        created["User"] = 1
    else:
        skipped["User"] = 1

    # --- Regiones ---
    for key, label in Region.REGIONES_CHOICES:
        safe_create(Region, {"nombre": key}, {"descripcion": f"Región {label}"})

    # --- Países ---
    ecuador = safe_create(PaisRegion, {"region": Region.objects.get(nombre="ecuador"), "nombre": "Ecuador"}, {
        "codigo_iso": "EC", "codigo_iso3": "ECU", "capital": "Quito",
        "bandera_png": "https://flagcdn.com/w320/ec.png", "bandera_svg": "https://flagcdn.com/ec.svg"
    })
    colombia = safe_create(PaisRegion, {"region": Region.objects.get(nombre="sudamerica"), "nombre": "Colombia"}, {
        "codigo_iso": "CO", "codigo_iso3": "COL", "capital": "Bogotá",
        "bandera_png": "https://flagcdn.com/w320/co.png", "bandera_svg": "https://flagcdn.com/co.svg"
    })
    peru = safe_create(PaisRegion, {"region": Region.objects.get(nombre="sudamerica"), "nombre": "Perú"}, {
        "codigo_iso": "PE", "codigo_iso3": "PER", "capital": "Lima",
        "bandera_png": "https://flagcdn.com/w320/pe.png", "bandera_svg": "https://flagcdn.com/pe.svg"
    })
    usa = safe_create(PaisRegion, {"region": Region.objects.get(nombre="norteamerica"), "nombre": "Estados Unidos"}, {
        "codigo_iso": "US", "codigo_iso3": "USA", "capital": "Washington D.C.",
        "bandera_png": "https://flagcdn.com/w320/us.png", "bandera_svg": "https://flagcdn.com/us.svg"
    })

    # --- Ciudades ---
    ciudades_data = [
        (ecuador, "Quito", "UIO", -0.1807, -78.4678, True),
        (ecuador, "Guayaquil", "GYE", -2.2038, -79.8976, False),
        (ecuador, "Cuenca", "CUE", -2.9006, -79.0046, False),
        (ecuador, "Manta", "MEC", -0.9677, -80.7089, False),
        (ecuador, "Galápagos", "GPS", -0.4534, -90.2656, False),
        (colombia, "Bogotá", "BOG", 4.7110, -74.0721, True),
        (colombia, "Medellín", "MDE", 6.2476, -75.5658, False),
        (peru, "Lima", "LIM", -12.0464, -77.0428, True),
        (peru, "Cusco", "CUZ", -13.5320, -71.9675, False),
        (usa, "Miami", "MIA", 25.7617, -80.1918, False),
        (usa, "Nueva York", "NYC", 40.7128, -74.0060, False),
        (usa, "Orlando", "ORL", 28.5383, -81.3792, False),
    ]
    for pais, nombre, codigo, lat, lng, capital in ciudades_data:
        safe_create(Ciudad, {"pais": pais, "codigo_ciudad": codigo}, {
            "nombre": nombre, "latitud": lat, "longitud": lng, "es_capital": capital
        })

    # --- Aerolíneas ---
    aerolineas_data = [
        ("LATAM Ecuador", "XL", "LNE", "Ecuador", "2016", "Aeropuerto Internacional José Joaquín de Olmedo (GYE)"),
        ("Avianca", "AV", "AVA", "Colombia", "1919", "Aeropuerto Internacional El Dorado (BOG)"),
        ("American Airlines", "AA", "AAL", "Estados Unidos", "1930", "Dallas/Fort Worth International Airport (DFW)"),
        ("United Airlines", "UA", "UAL", "Estados Unidos", "1926", "O'Hare International Airport (ORD)"),
        ("Delta Air Lines", "DL", "DAL", "Estados Unidos", "1924", "Hartsfield–Jackson Atlanta International Airport (ATL)"),
        ("Copa Airlines", "CM", "CMP", "Panamá", "1947", "Aeropuerto Internacional de Tocumen (PTY)"),
    ]
    for nombre, iata, icao, pais_origen, anio, base in aerolineas_data:
        safe_create(Aerolinea, {"codigo_iata": iata}, {
            "nombre": nombre, "codigo_icao": icao, "pais_origen": pais_origen,
            "anio_creacion": anio, "base_aeropuerto": base
        })

    # --- Aeropuertos ---
    aeropuertos_data = [
        ("UIO", "SEQU", "Aeropuerto Internacional Mariscal Sucre", "Quito", ecuador, -0.1292, -78.3575, 9228, "America/Guayaquil"),
        ("GYE", "SEGU", "Aeropuerto Internacional José Joaquín de Olmedo", "Guayaquil", ecuador, -2.1575, -79.8836, 19, "America/Guayaquil"),
        ("CUE", "SECU", "Aeropuerto Internacional Mariscal Lamar", "Cuenca", ecuador, -2.8894, -78.9844, 8306, "America/Guayaquil"),
        ("MEC", "SEMT", "Aeropuerto Internacional Eloy Alfaro", "Manta", ecuador, -0.9461, -80.6789, 48, "America/Guayaquil"),
        ("GPS", "SEGS", "Aeropuerto Seymour de Galápagos", "Galápagos", ecuador, -0.4538, -90.2659, 207, "Pacific/Galapagos"),
        ("BOG", "SKBO", "Aeropuerto Internacional El Dorado", "Bogotá", colombia, 4.7016, -74.1469, 8360, "America/Bogota"),
        ("MIA", "KMIA", "Aeropuerto Internacional de Miami", "Miami", usa, 25.7932, -80.2906, 8, "America/New_York"),
        ("JFK", "KJFK", "Aeropuerto Internacional John F. Kennedy", "Nueva York", usa, 40.6413, -73.7781, 13, "America/New_York"),
    ]
    for iata, icao, nombre, ciudad_nombre, pais, lat, lng, elev, tz in aeropuertos_data:
        ciudad_obj = Ciudad.objects.filter(codigo_ciudad=iata if iata in ["UIO","GYE","CUE","MEC","GPS","BOG","MIA","JFK"] else "ZZZ").first()
        safe_create(Aeropuerto, {"codigo_iata": iata}, {
            "codigo_icao": icao, "nombre": nombre,
            "pais": pais, "nombre_ciudad": ciudad_nombre,
            "latitud": lat, "longitud": lng, "elevacion_ft": elev, "zona_horaria": tz
        })

    # --- Tipos de Paquete ---
    for tipo in ["Aventura", "Relax", "Cultural", "Romántico", "Familiar", "Ecoturismo", "Luna de Miel"]:
        safe_create(TipoPaquete, {"nombre": tipo}, {})

    # --- Temporadas ---
    for temp in ["Alta", "Media", "Baja"]:
        safe_create(Temporada, {"nombre": temp}, {})

    # --- Tipos de Viaje ---
    for tv in ["Nacional", "Internacional"]:
        safe_create(TipoViaje, {"nombre": tv}, {})

    # --- Destinos ---
    destinos_data = [
        ("Quito Colonial", ecuador, "Descubre el centro histórico mejor preservado de América Latina, declarado Patrimonio de la Humanidad por la UNESCO. Disfruta de sus iglesias barrocas, plazas coloniales y la vibrante vida cultural quiteña.", 799.00, True),
        ("Guayaquil y el Malecón 2000", ecuador, "Recorre el Malecón Simón Bolívar, el Puerto Santa Ana y el Barrio Las Peñas. Vive la energía del principal puerto del Ecuador entre gastronomía, río y modernidad.", 599.00, True),
        ("Cuenca de los Andes", ecuador, "Sumérgete en la elegancia colonial de Cuenca, ciudad Patrimonio de la Humanidad. Calles adoquinadas, catedrales, tejidos de paja toquilla y el Parque Nacional Cajas.", 699.00, True),
        ("Galápagos - Naturaleza Viva", ecuador, "Explora el archipiélago único en el mundo. Tortugas gigantes, lobos marinos, piqueros de patas azules y paisajes volcánicos que inspiraron a Darwin.", 2499.00, True),
        ("Ruta del Spondylus - Costa Pacífica", ecuador, "Playas doradas, olas del Pacífico, mariscos frescos y atardeceres inolvidables. De Salinas a Manta, descubre la magia del perfil costero ecuatoriano.", 549.00, False),
        ("Amazonía - Yasuní", ecuador, "Adéntrate en la selva amazónica, el pulmón del planeta. Comunidades indígenas, ríos caudalosos y la biodiversidad más densa de la Tierra te esperan.", 1199.00, False),
        ("Nueva York - la Gran Manzana", usa, "Times Square, Central Park, la Estatua de la Libertad, Broadway. Vive la ciudad que nunca duerme con paquetes que incluyen vuelo, hotel y tours guiados.", 1899.00, False),
        ("Miami Beach", usa, "Playas de arena blanca, art déco, compras en Dolphin Mall y paseos en los Everglades. El destino favorito de los ecuatorianos para escapar del invierno.", 1499.00, False),
    ]
    for nombre, pais, descripcion, precio, destacado in destinos_data:
        safe_create(Destino, {"nombre": nombre, "pais": pais}, {
            "descripcion": descripcion, "precio_desde": precio, "destacado": destacado,
            "imagen_url": "https://images.unsplash.com/photo-1586016413664-9a3c0c04ab72?w=800"
        })

    # --- Paquetes Turísticos ---
    q = Ciudad.objects.get(codigo_ciudad="UIO")
    gye = Ciudad.objects.get(codigo_ciudad="GYE")
    aventura = TipoPaquete.objects.get(nombre="Aventura")
    relax = TipoPaquete.objects.get(nombre="Relax")
    cultural = TipoPaquete.objects.get(nombre="Cultural")
    temporada_alta = Temporada.objects.get(nombre="Alta")
    nacional = TipoViaje.objects.get(nombre="Nacional")
    internacional = TipoViaje.objects.get(nombre="Internacional")
    latam = Aerolinea.objects.get(codigo_iata="XL")

    paquetes_data = [
        {
            "titulo": "Galápagos Express",
            "subtitulo": "4 días / 3 noches",
            "descripcion_corta": "Descubre el archipiélago encantado con este paquete exprés.",
            "region": Region.objects.get(nombre="ecuador"),
            "pais_destino": ecuador,
            "ciudad_destino": Ciudad.objects.get(codigo_ciudad="GPS"),
            "precio": 1899.00,
            "tipo_paquete": aventura,
            "duracion_noches": 3,
            "duracion_dias": 4,
            "salidas": "Quito y Guayaquil",
            "fecha_salidas_texto": "Todo el año",
            "aerolinea": latam,
            "temporada": temporada_alta,
            "tipo_viaje": nacional,
            "destacado": True,
        },
        {
            "titulo": "Quito Colonial & Mitad del Mundo",
            "subtitulo": "3 días / 2 noches",
            "descripcion_corta": "Recorre el centro histórico de Quito y visita la Mitad del Mundo.",
            "region": Region.objects.get(nombre="ecuador"),
            "pais_destino": ecuador,
            "ciudad_destino": q,
            "precio": 499.00,
            "tipo_paquete": cultural,
            "duracion_noches": 2,
            "duracion_dias": 3,
            "salidas": "Guayaquil",
            "fecha_salidas_texto": "Todo el año",
            "aerolinea": latam,
            "temporada": temporada_alta,
            "tipo_viaje": nacional,
            "destacado": True,
        },
        {
            "titulo": "Sol y Playa - Salinas",
            "subtitulo": "3 días / 2 noches",
            "descripcion_corta": "Disfruta de las mejores playas del Pacífico ecuatoriano.",
            "region": Region.objects.get(nombre="ecuador"),
            "pais_destino": ecuador,
            "precio": 349.00,
            "tipo_paquete": relax,
            "duracion_noches": 2,
            "duracion_dias": 3,
            "salidas": "Quito y Guayaquil",
            "fecha_salidas_texto": "Enero a Diciembre",
            "aerolinea": latam,
            "temporada": temporada_alta,
            "tipo_viaje": nacional,
            "destacado": True,
        },
        {
            "titulo": "New York Dreams",
            "subtitulo": "5 días / 4 noches",
            "descripcion_corta": "Vive la magia de Nueva York con vuelo incluido.",
            "region": Region.objects.get(nombre="norteamerica"),
            "pais_destino": usa,
            "precio": 2599.00,
            "tipo_paquete": cultural,
            "duracion_noches": 4,
            "duracion_dias": 5,
            "salidas": "Quito y Guayaquil",
            "fecha_salidas_texto": "Enero a Diciembre",
            "tipo_viaje": internacional,
            "destacado": True,
        },
        {
            "titulo": "Miami Sunset",
            "subtitulo": "4 días / 3 noches",
            "descripcion_corta": "Playas, compras y diversión en el sur de Florida.",
            "region": Region.objects.get(nombre="norteamerica"),
            "pais_destino": usa,
            "precio": 1899.00,
            "tipo_paquete": relax,
            "duracion_noches": 3,
            "duracion_dias": 4,
            "salidas": "Quito y Guayaquil",
            "fecha_salidas_texto": "Febrero a Diciembre",
            "tipo_viaje": internacional,
            "destacado": True,
        },
    ]
    for p in paquetes_data:
        safe_create(PaqueteTuristico, {"titulo": p["titulo"], "pais_destino": p["pais_destino"]}, p)

    # --- ConfiguracionDestacados ---
    ConfiguracionDestacados.load()

    return JsonResponse({
        "status": "seed complete",
        "created": created,
        "skipped": skipped,
        "admin": {"user": "admin", "password": "Admin123!"}
    })