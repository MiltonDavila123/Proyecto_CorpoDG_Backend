from django.apps import AppConfig
import json
import os


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
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        self._crear_datos_iniciales()
    
    def _crear_datos_iniciales(self):
        """Crea regiones, países, ciudades y aerolíneas desde los archivos JSON"""
        from servicios.models import Region, PaisRegion, Ciudad, Aerolinea
        from django.conf import settings
        
        crear_geo = not Region.objects.exists()
        crear_aerolineas = not Aerolinea.objects.exists()
        
        if not crear_geo and not crear_aerolineas:
            return
        
        print("\n" + "=" * 60)
        print("Creando datos iniciales...")
        print("=" * 60)
        
        if not crear_geo:
            # Solo cargar aerolíneas
            self._cargar_aerolineas(settings.BASE_DIR)
            return
        
        # Rutas de los archivos JSON
        base_dir = settings.BASE_DIR
        paises_json_path = os.path.join(base_dir, 'nuevo_paises.json')
        ciudades_json_path = os.path.join(base_dir, 'ciudades.json')
        
        # Verificar que existan los archivos
        if not os.path.exists(paises_json_path):
            print(f"ERROR: No se encontró {paises_json_path}")
            return
        if not os.path.exists(ciudades_json_path):
            print(f"ERROR: No se encontró {ciudades_json_path}")
            return
        
        # =====================================================
        # PASO 1: Crear las regiones
        # =====================================================
        regiones_data = [
            ('caribe', 1),
            ('sudamerica', 2),
            ('centroamerica', 3),
            ('norteamerica', 4),
            ('europa', 5),
            ('medio_oriente', 6),
            ('africa', 7),
            ('asia', 8),
            ('oceania', 9),
            ('ecuador', 10),
        ]

        regiones_creadas = {}
        for nombre, orden in regiones_data:
            region, created = Region.objects.get_or_create(
                nombre=nombre, 
                defaults={'orden': orden}
            )
            regiones_creadas[nombre] = region
        
        print(f"✓ Regiones creadas: {Region.objects.count()}")
        
        # =====================================================
        # PASO 2: Cargar países desde nuevo_paises.json
        # =====================================================
        with open(paises_json_path, 'r', encoding='utf-8') as f:
            paises_data = json.load(f)
        
        # Diccionario para mapear codigo_iso -> PaisRegion
        paises_por_codigo = {}
        paises_count = 0
        
        for region_nombre, paises_lista in paises_data.items():
            region = regiones_creadas.get(region_nombre)
            if not region:
                print(f"  ADVERTENCIA: Región '{region_nombre}' no encontrada, saltando...")
                continue
            
            for pais_info in paises_lista:
                nombre_es = pais_info.get('nombre_es', '')
                codigo_iso = pais_info.get('codigo_iso', '')
                
                if not nombre_es:
                    continue
                
                pais, created = PaisRegion.objects.get_or_create(
                    region=region,
                    nombre=nombre_es,
                    defaults={
                        'nombre_en': pais_info.get('nombre_en', ''),
                        'codigo_iso': codigo_iso,
                        'codigo_iso3': pais_info.get('codigo_iso3', ''),
                        'capital': pais_info.get('capital', '') or '',
                        'bandera_png': pais_info.get('bandera_png', ''),
                        'bandera_svg': pais_info.get('bandera_svg', ''),
                    }
                )
                
                # Guardar en diccionario para búsqueda rápida
                if codigo_iso:
                    paises_por_codigo[codigo_iso] = pais
                
                if created:
                    paises_count += 1
        
        print(f"✓ Países creados: {paises_count}")
        
        # =====================================================
        # PASO 3: Cargar ciudades desde ciudades.json
        # =====================================================
        with open(ciudades_json_path, 'r', encoding='utf-8') as f:
            ciudades_data = json.load(f)
        
        ciudades_count = 0
        ciudades_sin_pais = 0
        capitales_marcadas = 0
        
        # Crear un set de capitales para marcarlas
        capitales = set()
        for paises_lista in paises_data.values():
            for pais_info in paises_lista:
                capital = pais_info.get('capital')
                if capital:
                    capitales.add(capital.lower())
        
        for ciudad_info in ciudades_data:
            country_code = ciudad_info.get('country_code', '')
            nombre = ciudad_info.get('name', '')
            city_code = ciudad_info.get('city_code', '')
            
            if not country_code or not nombre:
                continue
            
            # Buscar el país por código ISO
            pais = paises_por_codigo.get(country_code)
            
            if not pais:
                ciudades_sin_pais += 1
                continue
            
            # Verificar si es capital
            es_capital = nombre.lower() in capitales
            
            # Crear o actualizar la ciudad
            ciudad, created = Ciudad.objects.get_or_create(
                pais=pais,
                codigo_ciudad=city_code,
                defaults={
                    'nombre': nombre,
                    'latitud': ciudad_info.get('lat'),
                    'longitud': ciudad_info.get('lng'),
                    'es_capital': es_capital,
                }
            )
            
            if created:
                ciudades_count += 1
                if es_capital:
                    capitales_marcadas += 1
        
        print(f"✓ Ciudades creadas: {ciudades_count}")
        if capitales_marcadas > 0:
            print(f"  └─ Capitales identificadas: {capitales_marcadas}")
        if ciudades_sin_pais > 0:
            print(f"  └─ Ciudades sin país relacionado (omitidas): {ciudades_sin_pais}")
        
        # =====================================================
        # PASO 4: Cargar aerolíneas desde aerolineas_full_data.json
        # =====================================================
        self._cargar_aerolineas(base_dir)
        
        print("=" * 60)
        print("Resumen final:")
        print(f"  • Regiones: {Region.objects.count()}")
        print(f"  • Países: {PaisRegion.objects.count()}")
        print(f"  • Ciudades: {Ciudad.objects.count()}")
        from servicios.models import Aerolinea
        print(f"  • Aerolíneas: {Aerolinea.objects.count()}")
        print("=" * 60 + "\n")

    def _cargar_aerolineas(self, base_dir):
        """Carga aerolíneas desde aerolineas_full_data.json preservando relaciones existentes"""
        from servicios.models import Aerolinea
        
        aerolineas_json_path = os.path.join(base_dir, 'aerolineas_full_data.json')
        
        if not os.path.exists(aerolineas_json_path):
            print(f"  ADVERTENCIA: No se encontró {aerolineas_json_path}")
            return
        
        with open(aerolineas_json_path, 'r', encoding='utf-8') as f:
            aerolineas_data = json.load(f)
        
        creadas = 0
        actualizadas = 0
        sin_iata = 0
        
        for aerolinea_info in aerolineas_data:
            nombre = aerolinea_info.get('name', '').strip()
            iata = aerolinea_info.get('iata', '').strip()
            icao = aerolinea_info.get('icao', '').strip()
            pais = aerolinea_info.get('country', '').strip()
            anio = aerolinea_info.get('year_created', '').strip()
            base = aerolinea_info.get('base', '').strip()
            logo = aerolinea_info.get('logo_url', '').strip()
            brandmark = aerolinea_info.get('brandmark_url', '').strip()
            
            if not nombre:
                continue
            
            # Si tiene código IATA, usar como clave para update_or_create
            # Esto preserva las relaciones FK existentes (Vuelo, PaqueteTuristico)
            if iata:
                aerolinea, created = Aerolinea.objects.update_or_create(
                    codigo_iata=iata,
                    defaults={
                        'nombre': nombre,
                        'codigo_icao': icao,
                        'pais_origen': pais,
                        'anio_creacion': anio,
                        'base_aeropuerto': base,
                        'logo_url': logo or None,
                        'brandmark_url': brandmark or None,
                    }
                )
            else:
                # Sin IATA, buscar por nombre exacto o crear
                aerolinea, created = Aerolinea.objects.update_or_create(
                    nombre=nombre,
                    codigo_iata='',
                    defaults={
                        'codigo_icao': icao,
                        'pais_origen': pais,
                        'anio_creacion': anio,
                        'base_aeropuerto': base,
                        'logo_url': logo or None,
                        'brandmark_url': brandmark or None,
                    }
                )
                sin_iata += 1
            
            if created:
                creadas += 1
            else:
                actualizadas += 1
        
        print(f"✓ Aerolíneas cargadas: {creadas} nuevas, {actualizadas} actualizadas")
        if sin_iata > 0:
            print(f"  └─ Aerolíneas sin código IATA: {sin_iata}")
