from django.apps import AppConfig


class ServiciosConfig(AppConfig):
    name = 'servicios'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Se ejecuta cuando la app está lista - crea datos iniciales si no existen"""
        import sys
        
        # Solo ejecutar con runserver, no con migrate u otros comandos
        if 'runserver' not in sys.argv:
            return
            
        # Evitar doble ejecución por el reloader
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        self._crear_datos_iniciales()
    
    def _crear_datos_iniciales(self):
        """Crea regiones y países si no existen"""
        from servicios.models import Region, PaisRegion
        
        # Si ya existen regiones, no hacer nada
        if Region.objects.exists():
            return
        
        print("\n" + "=" * 60)
        print("Creando datos iniciales (regiones y países)...")
        print("=" * 60)
        
        # Crear las regiones
        regiones_data = [
            ('caribe', 1),
            ('sudamerica', 2),
            ('centroamerica', 3),
            ('norteamerica', 4),
            ('europa', 5),
            ('medio_oriente', 6),
            ('africa', 7),
            ('asia', 8),
            ('ecuador', 9),
        ]

        for nombre, orden in regiones_data:
            Region.objects.get_or_create(nombre=nombre, defaults={'orden': orden})

        # SOLO PAÍSES (sin ciudades)
        paises_por_region = {
            'caribe': [
                'Aruba', 'Bahamas', 'Cuba', 'Curazao', 'Jamaica',
                'Puerto Rico', 'República Dominicana', 'San Martín',
                'Trinidad y Tobago', 'Islas Vírgenes'
            ],
            'sudamerica': [
                'Argentina', 'Bolivia', 'Brasil', 'Chile', 'Colombia'
                ,'Paraguay', 'Perú', 'Uruguay', 'Venezuela'
            ],
            'centroamerica': [
                'Belice', 'Costa Rica', 'El Salvador', 'Guatemala',
                'Honduras', 'Nicaragua', 'Panamá'
            ],
            'norteamerica': [
                'Canadá', 'Estados Unidos', 'México'
            ],
            'europa': [
                'Alemania', 'Austria', 'Bélgica', 'Croacia', 'España',
                'Francia', 'Grecia', 'Hungría', 'Italia', 'Países Bajos',
                'Polonia', 'Portugal', 'Reino Unido', 'República Checa',
                'Rusia', 'Suiza', 'Turquía'
            ],
            'asia': [
                'China', 'Corea del Sur', 'Filipinas', 'India', 'Indonesia',
                'Japón', 'Malasia', 'Maldivas', 'Singapur', 'Tailandia',
                'Vietnam'
            ],
            'medio_oriente': [
                'Arabia Saudita', 'Egipto', 'Emiratos Árabes Unidos',
                'Israel', 'Jordania', 'Qatar', 'Uzbekistán'
            ],
            'africa': [
                'Egipto', 'Kenia', 'Marruecos', 'Sudáfrica', 'Tanzania'
            ],
            'ecuador': [
                'Ecuador'
            ],
        }

        for region_nombre, paises in paises_por_region.items():
            try:
                region = Region.objects.get(nombre=region_nombre)
                for pais_nombre in paises:
                    PaisRegion.objects.get_or_create(
                        region=region,
                        nombre=pais_nombre
                    )
            except Region.DoesNotExist:
                pass

        print(f"Regiones creadas: {Region.objects.count()}")
        print(f"Países creados: {PaisRegion.objects.count()}")
        print("=" * 60 + "\n")
