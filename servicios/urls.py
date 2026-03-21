from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet)
router.register(r'solicitudes', views.SolicitudViewSet)
router.register(r'destinos', views.DestinoViewSet)
router.register(r'vuelos', views.VueloViewSet)

# Paquetes Turísticos
router.register(r'regiones', views.RegionViewSet)
router.register(r'paises-region', views.PaisRegionViewSet)
router.register(r'ciudades', views.CiudadViewSet)
router.register(r'aerolineas', views.AerolineaViewSet)
router.register(r'aeropuertos', views.AeropuertoViewSet)
router.register(r'paquetes', views.PaqueteTuristicoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('contacto/', views.contacto, name='contacto'),
    path('buscar-vuelos-live/', views.BuscadorVuelosSabreView.as_view(), name='buscar_vuelos_live'),
    # Endpoints AJAX para admin
    path('admin-ajax/paises-por-region/<int:region_id>/', views.paises_por_region, name='ajax_paises'),
    path('admin-ajax/ciudades-por-pais/<int:pais_id>/', views.ciudades_por_pais, name='ajax_ciudades'),
    path('admin-ajax/aeropuertos-por-ciudad/<int:ciudad_id>/', views.aeropuertos_por_ciudad, name='ajax_aeropuertos_ciudad'),
    path('admin-ajax/aeropuertos-por-pais/<int:pais_id>/', views.aeropuertos_por_pais, name='ajax_aeropuertos_pais'),
]
