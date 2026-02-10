from django.db import models
from django.core.exceptions import ValidationError
import re


def validate_google_drive_pdf(value):
    """Validador para asegurar que sea un link de Google Drive válido"""
    if not value:   
        return value
    
    # Patrón para validar links de Google Drive
    google_drive_pattern = r'^https://drive\.google\.com/file/d/[a-zA-Z0-9_-]+/(view|edit|preview)(\?.*)?$'
    
    if not re.match(google_drive_pattern, value):
        raise ValidationError(
            'El link debe ser un URL válido de Google Drive. '
            'Ejemplo: https://drive.google.com/file/d/ID_DEL_ARCHIVO/view'
        )
    
    return value


def normalize_google_drive_url(url):
    """Normaliza la URL de Google Drive para que termine en /preview"""
    if not url:
        return url
    
    # Reemplazar /view o /edit por /preview
    url = re.sub(r'/(view|edit)(\?.*)?$', '/preview', url)
    
    return url


class GoogleDrivePDFMixin:
    """Mixin para normalizar URLs de Google Drive en el campo pdf_url"""
    
    def clean(self):
        super().clean()
        if hasattr(self, 'pdf_url') and self.pdf_url:
            self.pdf_url = normalize_google_drive_url(self.pdf_url)
    
    def save(self, *args, **kwargs):
        if hasattr(self, 'pdf_url') and self.pdf_url:
            self.pdf_url = normalize_google_drive_url(self.pdf_url)
        super().save(*args, **kwargs)


class Cliente(models.Model):
    """Modelo para almacenar información básica del cliente"""
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


class Destino(GoogleDrivePDFMixin, models.Model):
    """Modelo para destinos turísticos"""
    nombre = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen_url = models.URLField(max_length=500)
    precio_desde = models.DecimalField(max_digits=10, decimal_places=2)
    destacado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    pdf_url = models.URLField(max_length=500, blank=True, null=True, validators=[validate_google_drive_pdf], help_text="URL del PDF de Google Drive (se convertirá a /preview automáticamente)")
    mensaje_reserva = models.TextField(blank=True, help_text="Mensaje predefinido para reserva/contacto")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'
        ordering = ['-destacado', 'nombre']

    def __str__(self):
        return f"{self.nombre}, {self.pais}"


class Hotel(GoogleDrivePDFMixin, models.Model):
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
    pdf_url = models.URLField(max_length=500, blank=True, null=True, validators=[validate_google_drive_pdf], help_text="URL del PDF de Google Drive (se convertirá a /preview automáticamente)")
    mensaje_reserva = models.TextField(blank=True, help_text="Mensaje predefinido para reserva/contacto")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hotel'
        verbose_name_plural = 'Hoteles'
        ordering = ['destino', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.destino.nombre}"


class Vuelo(GoogleDrivePDFMixin, models.Model):
    """Modelo para vuelos"""
    TIPO_VUELO = [
        ('directo', 'Directo'),
        ('escala', 'Con Escala'),
    ]
    
    aerolinea = models.ForeignKey(
        'Aerolinea', 
        on_delete=models.CASCADE, 
        related_name='vuelos'
    )
    origen = models.ForeignKey(
        'Ciudad',
        on_delete=models.CASCADE,
        related_name='vuelos_origen'
    )
    destino = models.ForeignKey(
        'Ciudad',
        on_delete=models.CASCADE,
        related_name='vuelos_destino'
    )
    
    tipo_vuelo = models.CharField(max_length=10, choices=TIPO_VUELO)
    numero_vuelo = models.CharField(max_length=20, blank=True, help_text="Ej: AA1234")
    duracion = models.CharField(max_length=50, help_text="Ej: 1h 45m")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    moneda = models.CharField(max_length=3, default='USD')
    disponible = models.BooleanField(default=True)
    pdf_url = models.URLField(max_length=500, blank=True, null=True, validators=[validate_google_drive_pdf], help_text="URL del PDF de Google Drive (se convertirá a /preview automáticamente)")
    mensaje_reserva = models.TextField(blank=True, help_text="Mensaje predefinido para reserva/contacto")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vuelo'
        verbose_name_plural = 'Vuelos'
        ordering = ['aerolinea', 'origen', 'destino']

    def __str__(self):
        return f"{self.aerolinea.nombre}: {self.origen.nombre} → {self.destino.nombre}"


class RentaAuto(GoogleDrivePDFMixin, models.Model):
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
    
    ciudad = models.ForeignKey(
        'Ciudad',
        on_delete=models.CASCADE,
        related_name='autos_renta'
    )
    direccion = models.CharField(max_length=300, blank=True, help_text="Dirección específica de recogida")
    
    caracteristicas = models.TextField(help_text="Características separadas por comas")
    disponible = models.BooleanField(default=True)
    pdf_url = models.URLField(max_length=500, blank=True, null=True, validators=[validate_google_drive_pdf], help_text="URL del PDF de Google Drive (se convertirá a /preview automáticamente)")
    mensaje_reserva = models.TextField(blank=True, help_text="Mensaje predefinido para reserva/contacto")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Renta de Auto'
        verbose_name_plural = 'Renta de Autos'
        ordering = ['tipo', 'marca']

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano}) - {self.ciudad.nombre}"


# =====================================================
# MODELOS PARA PAQUETES TURÍSTICOS
# =====================================================

class Region(models.Model):
    """Modelo para las regiones geográficas"""
    REGIONES_CHOICES = [
        ('caribe', 'Caribe'),
        ('sudamerica', 'Sudamérica'),
        ('centroamerica', 'Centroamérica'),
        ('norteamerica', 'Norteamérica'),
        ('europa', 'Europa'),
        ('medio_oriente', 'Medio Oriente'),
        ('africa', 'África'),
        ('asia', 'Asia'),
        ('ecuador', 'Ecuador'),
    ]
    
    nombre = models.CharField(max_length=50, choices=REGIONES_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0, help_text="Orden de aparición")
    
    class Meta:
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.get_nombre_display()


class PaisRegion(models.Model):
    """Modelo para los países/destinos dentro de cada región"""
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='paises')
    nombre = models.CharField(max_length=100)
    codigo_pais = models.CharField(max_length=3, blank=True, help_text="Código ISO del país (ej: USA, ECU)")
    bandera_url = models.URLField(max_length=500, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'País/Destino de Región'
        verbose_name_plural = 'Países/Destinos de Región'
        ordering = ['region', 'nombre']
        unique_together = ['region', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.region.get_nombre_display()})"


class Ciudad(models.Model):
    """Modelo para ciudades dentro de cada país"""
    pais = models.ForeignKey(PaisRegion, on_delete=models.CASCADE, related_name='ciudades')
    nombre = models.CharField(max_length=100)
    codigo_aeropuerto = models.CharField(max_length=5, blank=True, help_text="Código IATA del aeropuerto principal (ej: GYE, UIO)")
    es_capital = models.BooleanField(default=False)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        ordering = ['pais', '-es_capital', 'nombre']
        unique_together = ['pais', 'nombre']
    
    def __str__(self):
        return f"{self.nombre}, {self.pais.nombre}"
    
    @property
    def ubicacion_completa(self):
        """Retorna Ciudad, País, Región"""
        return f"{self.nombre}, {self.pais.nombre} ({self.pais.region.get_nombre_display()})"


class Aerolinea(models.Model):
    """Modelo para aerolíneas"""
    nombre = models.CharField(max_length=100)
    codigo_iata = models.CharField(max_length=3, blank=True, help_text="Código IATA de 2-3 letras (ej: AA, LA, AV)")
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    pais_origen = models.CharField(max_length=100, blank=True, help_text="País de origen de la aerolínea")
    sitio_web = models.URLField(max_length=300, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Aerolínea'
        verbose_name_plural = 'Aerolíneas'
        ordering = ['nombre']
    
    def __str__(self):
        if self.codigo_iata:
            return f"{self.nombre} ({self.codigo_iata})"
        return self.nombre


class PaqueteTuristico(GoogleDrivePDFMixin, models.Model):
    """Modelo principal para paquetes turísticos"""
    
    TIPO_PAQUETE_CHOICES = [
        ('vacaciones', 'Vacaciones'),
        ('promo', 'Promo'),
        ('oferta', 'Oferta'),
        ('todo_incluido', 'Todo Incluido'),
        ('aventura', 'Aventura'),
        ('luna_miel', 'Luna de Miel'),
        ('familiar', 'Familiar'),
        ('negocios', 'Negocios'),
    ]
    
    TEMPORADA_CHOICES = [
        ('baja', 'Temporada Baja'),
        ('media', 'Temporada Media'),
        ('alta', 'Temporada Alta'),
    ]
    
    TIPO_VIAJE_CHOICES = [
        ('familiar', 'Viajes de familia'),
        ('pareja', 'Viajes en pareja'),
        ('amigos', 'Viajes con amigos'),
        ('solo', 'Viaje solo'),
        ('negocios', 'Viaje de negocios'),
        ('aventura', 'Viaje de aventura'),
    ]
    
    # === INFORMACIÓN BÁSICA DEL CARD ===
    titulo = models.CharField(max_length=200, help_text="Título del paquete para el card")
    subtitulo = models.CharField(max_length=200, blank=True, help_text="Subtítulo o info adicional (ej: Enero a Diciembre)")
    imagen_url = models.URLField(max_length=500, help_text="Imagen principal del card")
    descripcion_corta = models.TextField(max_length=500, help_text="Descripción breve para el card")
    
    # === UBICACIÓN Y DESTINO ===
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='paquetes')
    pais_destino = models.ForeignKey(PaisRegion, on_delete=models.CASCADE, related_name='paquetes')
    ciudad_destino = models.ForeignKey(
        Ciudad, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='paquetes',
        help_text="Ciudad específica del destino"
    )
    
    # === PRECIOS Y TIPO ===
    precio = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio desde")
    moneda = models.CharField(max_length=3, default='USD')
    tipo_paquete = models.CharField(max_length=20, choices=TIPO_PAQUETE_CHOICES, default='vacaciones')
    
    # === DURACIÓN Y FECHAS ===
    duracion_noches = models.IntegerField(help_text="Número de noches")
    duracion_dias = models.IntegerField(default=1, help_text="Número de días")
    salidas = models.CharField(max_length=200, help_text="Ej: Quito y Guayaquil")
    fecha_salidas_texto = models.CharField(max_length=100, blank=True, help_text="Ej: 2025 Enero a Diciembre")
    
    # === AEROLÍNEA ===
    aerolinea = models.ForeignKey(Aerolinea, on_delete=models.SET_NULL, null=True, blank=True, related_name='paquetes')
    
    # === INFORMACIÓN DETALLADA (PÁGINA DEL PAQUETE) ===
    titulo_detalle = models.CharField(max_length=300, blank=True, help_text="Título principal en la página de detalle")
    descripcion_extensa = models.TextField(blank=True, help_text="Descripción completa del paquete")
    
    # === DETALLES DEL DESTINO (Lateral) ===
    temporada = models.CharField(max_length=10, choices=TEMPORADA_CHOICES, default='baja')
    tipo_viaje = models.CharField(max_length=20, choices=TIPO_VIAJE_CHOICES, default='familiar')
    precio_aplica_desde = models.DateField(null=True, blank=True, help_text="Fecha desde que aplica el precio")
    precio_aplica_hasta = models.DateField(null=True, blank=True, help_text="Fecha hasta que aplica el precio")
    
    # === INFORMACIÓN DEL DESTINO (Para sidebar) ===
    ubicacion_mapa_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL de imagen del mapa")
    idioma = models.CharField(max_length=100, blank=True, help_text="Ej: Oficial Inglés USA")
    moneda_local = models.CharField(max_length=100, blank=True, help_text="Ej: Dólar Americano")
    lugares_destacados = models.TextField(blank=True, help_text="Lugares destacados separados por comas")
    documentos_requeridos = models.TextField(blank=True, help_text="Ej: Visa Americana. Pasaporte vigente.")
    temperatura = models.CharField(max_length=50, blank=True, help_text="Ej: 23°C - 28°C")
    
    # === SECCIONES DE TEXTO (TextFields para cada sección) ===
    programa_incluye = models.TextField(blank=True, help_text="Qué incluye el programa")
    no_incluye = models.TextField(blank=True, help_text="Qué NO incluye el paquete")
    como_reservar = models.TextField(blank=True, help_text="Instrucciones para reservar")
    importante = models.TextField(blank=True, help_text="Información importante")
    horarios_vuelo = models.TextField(blank=True, help_text="Horarios de vuelos")
    politicas_equipaje = models.TextField(blank=True, help_text="Políticas de equipaje")
    requisitos_viaje = models.TextField(blank=True, help_text="Requisitos para el viaje")
    formas_pago = models.TextField(blank=True, help_text="Formas de pago aceptadas")
    politica_cancelacion = models.TextField(blank=True, help_text="Política de cancelación")
    
    # === PAQUETE INCLUYE (Iconos) ===
    incluye_vuelo = models.BooleanField(default=True, help_text="¿Incluye vuelo?")
    incluye_hotel = models.BooleanField(default=True, help_text="¿Incluye hotel?")
    incluye_alimentacion = models.BooleanField(default=False, help_text="¿Incluye alimentación?")
    incluye_traslados = models.BooleanField(default=False, help_text="¿Incluye traslados?")
    incluye_tours = models.BooleanField(default=False, help_text="¿Incluye tours?")
    incluye_seguro = models.BooleanField(default=False, help_text="¿Incluye seguro?")
    
    # === PDF Y CONTACTO ===
    pdf_url = models.URLField(max_length=500, blank=True, null=True, validators=[validate_google_drive_pdf], help_text="URL del PDF de Google Drive (se convertirá a /preview automáticamente)")
    mensaje_reserva = models.TextField(blank=True, help_text="Mensaje predefinido para reserva/contacto")
    
    # === ESTADO Y FECHAS ===
    destacado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Paquete Turístico'
        verbose_name_plural = 'Paquetes Turísticos'
        ordering = ['-destacado', '-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.pais_destino.nombre}"
    
    @property
    def texto_paquete(self):
        """Genera el texto 'Paquete a [destino], Tour de [X] noches mínimo'"""
        return f"Paquete a {self.pais_destino.nombre}, Tour de {self.duracion_noches} noches mínimo"
    
    @property
    def destino_completo(self):
        """Retorna la región y destino completo"""
        ciudad = self.ciudad_destino.nombre if self.ciudad_destino else self.pais_destino.nombre
        return f"{self.region.get_nombre_display()} - {ciudad}"
