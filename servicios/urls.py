from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet)
router.register(r'solicitudes', views.SolicitudViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('contacto/', views.contacto, name='contacto'),
]
