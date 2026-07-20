"""
URL configuration for corpodg project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from servicios.views import (
    admin_dashboard, admin_exportar_reservas,
    admin_carga_masiva, admin_descargar_plantilla,
)

urlpatterns = [
    # Deben ir antes de admin/ para que el admin no capture las rutas
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/exportar-reservas/', admin_exportar_reservas, name='admin_exportar_reservas'),
    path('admin/carga-masiva/', admin_carga_masiva, name='admin_carga_masiva'),
    path('admin/carga-masiva/plantilla/<str:tipo>/', admin_descargar_plantilla,
         name='admin_descargar_plantilla'),
    path('admin/', admin.site.urls),
    path('api/', include('servicios.urls')),
]
