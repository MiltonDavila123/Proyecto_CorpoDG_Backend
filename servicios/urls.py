from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet)
router.register(r'solicitudes', views.SolicitudViewSet)
router.register(r'destinos', views.DestinoViewSet)
router.register(r'hoteles', views.HotelViewSet)
router.register(r'vuelos', views.VueloViewSet)
router.register(r'renta-autos', views.RentaAutoViewSet)

# Paquetes Turísticos
router.register(r'regiones', views.RegionViewSet)
router.register(r'paises-region', views.PaisRegionViewSet)
router.register(r'ciudades', views.CiudadViewSet)
router.register(r'aerolineas', views.AerolineaViewSet)
router.register(r'paquetes', views.PaqueteTuristicoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('contacto/', views.contacto, name='contacto'),
    # Endpoints AJAX para admin
    path('admin-ajax/paises-por-region/<int:region_id>/', views.paises_por_region, name='paises_por_region'),
    path('admin-ajax/ciudades-por-pais/<int:pais_id>/', views.ciudades_por_pais, name='ciudades_por_pais'),
]
