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
router.register(r'mensajes', views.MensajeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('contacto/', views.contacto, name='contacto'),
]
