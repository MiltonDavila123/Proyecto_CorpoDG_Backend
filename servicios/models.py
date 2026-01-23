from django.db import models


class Cliente(models.Model):
    """Modelo para almacenar información básica del cliente"""
    #Creamos los modelos del Cliente
    nombre_completo = models.CharField(max_length=50)
    email = models.EmailField(max_length=80, unique=True)
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nombre_completo} - {self.email}"


class Solicitud(models.Model):
    """Modelo para almacenar las solicitudes/mensajes de los clientes"""
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='solicitudes'
    )
    mensaje = models.TextField(max_length=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    atendido = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Solicitud'
        verbose_name_plural = 'Solicitudes'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Solicitud de {self.cliente.nombre_completo} - {self.fecha_creacion.strftime('%Y-%m-%d')}"
