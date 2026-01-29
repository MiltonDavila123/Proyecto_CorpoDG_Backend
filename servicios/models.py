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


class Destino(models.Model):
    """Modelo para destinos turísticos"""
    nombre = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen_url = models.URLField(max_length=500)
    precio_desde = models.DecimalField(max_digits=10, decimal_places=2)
    destacado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'
        ordering = ['-destacado', 'nombre']

    def __str__(self):
        return f"{self.nombre}, {self.pais}"


class Hotel(models.Model):
    """Modelo para hoteles"""
    nombre = models.CharField(max_length=200)
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE, related_name='hoteles')
    descripcion = models.TextField()
    imagen_url = models.URLField(max_length=500)
    direccion = models.CharField(max_length=300)
    estrellas = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    precio_noche = models.DecimalField(max_digits=10, decimal_places=2)
    servicios = models.TextField(help_text="Servicios separados por comas (Wi-Fi, Piscina, etc.)")
    disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hotel'
        verbose_name_plural = 'Hoteles'
        ordering = ['destino', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.destino.nombre}"


class Vuelo(models.Model):
    """Modelo para vuelos"""
    TIPO_VUELO = [
        ('directo', 'Directo'),
        ('escala', 'Con Escala'),
    ]
    
    aerolinea = models.CharField(max_length=100)
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    tipo_vuelo = models.CharField(max_length=10, choices=TIPO_VUELO)
    duracion = models.CharField(max_length=50, help_text="Ej: 1h 45m")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen_url = models.URLField(max_length=500)
    moneda = models.CharField(max_length=3, default='USD')
    disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vuelo'
        verbose_name_plural = 'Vuelos'
        ordering = ['origen', 'destino']

    def __str__(self):
        return f"{self.aerolinea}: {self.origen} → {self.destino}"


class RentaAuto(models.Model):
    """Modelo para renta de autos"""
    TIPO_AUTO = [
        ('economico', 'Económico'),
        ('sedan', 'Sedán'),
        ('suv', 'SUV'),
        ('lujo', 'Lujo'),
        ('van', 'Van'),
    ]
    
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_AUTO)
    ano = models.IntegerField()
    capacidad_pasajeros = models.IntegerField()
    transmision = models.CharField(max_length=20, choices=[('manual', 'Manual'), ('automatica', 'Automática')])
    precio_dia = models.DecimalField(max_digits=10, decimal_places=2)
    imagen_url = models.URLField(max_length=500)
    ubicacion = models.CharField(max_length=200)
    caracteristicas = models.TextField(help_text="Características separadas por comas")
    disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Renta de Auto'
        verbose_name_plural = 'Renta de Autos'
        ordering = ['tipo', 'marca']

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano})"


class Mensaje(models.Model):
    """Modelo para mensajes de contacto generales"""
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=15, blank=True)
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    respondido = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"{self.nombre} - {self.asunto} ({self.fecha_envio.strftime('%Y-%m-%d')})"
