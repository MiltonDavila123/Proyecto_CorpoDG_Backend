import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from servicios.models import (
    Region, PaisRegion, Ciudad, Aerolinea, Aeropuerto,
    Vuelo, TipoPaquete, Temporada, TipoViaje,
    PaqueteTuristico, Destino, ConfiguracionDestacados
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = BASE_DIR / "servicios" / "Scripts"

def load_json(filename):
    with open(SCRIPTS_DIR / filename, encoding="utf-8") as f:
        return json.load(f)

class Command(BaseCommand):
    help = "Puebla la base de datos con datos de prueba"

    def handle(self, *args, **options):
        self._create_superuser()
        self._create_config()
        self._create_regions()
        self._create_countries()
        self._create_cities()
        self._create_airlines()
        self._create_airports()
        self._create_flights()
        self._create_tipos()
        self._create_temporadas()
        self._create_tipos_viaje()
        self._create_destinos()
        self._create_paquetes()
        self.stdout.write(self.style.SUCCESS("Seed completado exitosamente"))

    def _create_superuser(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@corpodg.com", "admin123")
            self.stdout.write("Superusuario creado: admin / admin123")

    def _create_config(self):
        ConfiguracionDestacados.load()
        self.stdout.write("ConfiguracionDestacados lista")

    def _create_regions(self):
        regiones_data = load_json("nuevo_paises.json")
        for nombre_key in regiones_data:
            nombre_display = {
                "caribe": "Caribe",
                "sudamerica": "Sudamérica",
                "centroamerica": "Centroamérica",
                "norteamerica": "Norteamérica",
                "europa": "Europa",
                "medio_oriente": "Medio Oriente",
                "africa": "África",
                "asia": "Asia",
                "oceania": "Oceanía",
                "ecuador": "Ecuador",
            }.get(nombre_key, nombre_key)
            Region.objects.get_or_create(
                nombre=nombre_key,
                defaults={"descripcion": f"Región {nombre_display}", "orden": len(regiones_data)}
            )
        self.stdout.write(f"Regiones creadas: {Region.objects.count()}")

    def _create_countries(self):
        regiones_data = load_json("nuevo_paises.json")
        for nombre_key, paises in regiones_data.items():
            region = Region.objects.get(nombre=nombre_key)
            for p in paises:
                PaisRegion.objects.get_or_create(
                    region=region, nombre=p["nombre_es"],
                    defaults={
                        "nombre_en": p.get("nombre_en", "") or "",
                        "codigo_iso": p.get("codigo_iso", "") or "",
                        "codigo_iso3": p.get("codigo_iso3", "") or "",
                        "capital": p.get("capital") or "",
                        "bandera_png": p.get("bandera_png", "") or "",
                        "bandera_svg": p.get("bandera_svg", "") or "",
                    }
                )
        self.stdout.write(f"Países creados: {PaisRegion.objects.count()}")

    def _create_cities(self):
        ec = PaisRegion.objects.filter(codigo_iso="EC").first()
        us = PaisRegion.objects.filter(codigo_iso="US").first()
        es = PaisRegion.objects.filter(codigo_iso="ES").first()
        mx = PaisRegion.objects.filter(codigo_iso="MX").first()
        co = PaisRegion.objects.filter(codigo_iso="CO").first()
        pa = PaisRegion.objects.filter(codigo_iso="PA").first()

        ciudades_data = [
            (ec, "Guayaquil", "GYE", -2.1578, -79.8833, True),
            (ec, "Quito", "UIO", -0.1807, -78.4678, True),
            (ec, "Cuenca", "CUE", -2.9006, -79.0042),
            (ec, "Manta", "MEC", -0.9461, -80.6789),
            (ec, "Galápagos (Baltra)", "GPS", -0.4531, -90.2644),
            (ec, "Santa Cruz (San Cristóbal)", "SCY", -0.9103, -89.6078),
            (ec, "Coca", "OCC", -0.4625, -76.9864),
            (ec, "Loja", "LOH", -3.9931, -79.2044),
            (ec, "Tena", "TNW", -0.9833, -77.8167),
            (us, "Miami", "MIA", 25.7617, -80.1918, False, True),
            (us, "New York", "NYC", 40.7128, -74.0060, False, True),
            (us, "Orlando", "ORL", 28.5383, -81.3792),
            (us, "Los Angeles", "LAX", 34.0522, -118.2437),
            (es, "Madrid", "MAD", 40.4168, -3.7038, False, True),
            (es, "Barcelona", "BCN", 41.3874, 2.1686),
            (mx, "Cancún", "CUN", 21.1619, -86.8515),
            (mx, "Ciudad de México", "MEX", 19.4326, -99.1332),
            (co, "Bogotá", "BOG", 4.7110, -74.0721),
            (pa, "Ciudad de Panamá", "PTY", 8.9824, -79.5199),
        ]
        for pais, nombre, codigo, lat, lng, *flags in ciudades_data:
            if pais:
                Ciudad.objects.get_or_create(
                    pais=pais, codigo_ciudad=codigo,
                    defaults={
                        "nombre": nombre,
                        "latitud": lat,
                        "longitud": lng,
                        "es_capital": flags[0] if flags else False,
                    }
                )
        self.stdout.write(f"Ciudades creadas: {Ciudad.objects.count()}")

    def _create_airlines(self):
        aerolineas_data = load_json("aerolineas_full_data.json")
        for a in aerolineas_data:
            Aerolinea.objects.get_or_create(
                nombre=a.get("nombre") or a.get("name", ""),
                defaults={
                    "codigo_iata": a.get("codigo_iata") or a.get("iata_code", ""),
                    "codigo_icao": a.get("codigo_icao") or a.get("icao_code", ""),
                    "pais_origen": a.get("pais_origen") or a.get("country_name", ""),
                    "logo_url": a.get("logo_url", ""),
                }
            )
        self.stdout.write(f"Aerolíneas creadas: {Aerolinea.objects.count()}")

    def _create_airports(self):
        try:
            aeropuertos_data = load_json("aeropuertos_full_data copy.json")
        except (FileNotFoundError, json.JSONDecodeError):
            aeropuertos_data = load_json("aeropuertos_full_data.json")

        for ap in aeropuertos_data:
            codigo_iata = (ap.get("iata") or "").strip().upper()
            if len(codigo_iata) != 3:
                continue
            pais_iso = ap.get("country", "").strip().upper()
            pais = PaisRegion.objects.filter(codigo_iso=pais_iso).first()
            if not pais:
                continue
            nombre_ciudad = ap.get("city", "") or ""
            ciudad_obj = None
            if nombre_ciudad:
                ciudad_obj = Ciudad.objects.filter(
                    pais=pais, nombre__icontains=nombre_ciudad[:30]
                ).first()
            nombre_ap = ap.get("name", "") or ""
            lat = ap.get("latitude")
            lon = ap.get("longitude")
            Aeropuerto.objects.get_or_create(
                codigo_iata=codigo_iata,
                defaults={
                    "codigo_icao": ap.get("icao", "") or "",
                    "nombre": nombre_ap,
                    "ciudad": ciudad_obj,
                    "pais": pais,
                    "nombre_ciudad": nombre_ciudad if not ciudad_obj else "",
                    "region": ap.get("region", "") or "",
                    "latitud": float(lat) if lat else None,
                    "longitud": float(lon) if lon else None,
                }
            )
        self.stdout.write(f"Aeropuertos creados: {Aeropuerto.objects.count()}")

    def _create_flights(self):
        if Vuelo.objects.exists():
            return
        aerolineas = list(Aerolinea.objects.filter(activo=True))
        aeropuertos = list(Aeropuerto.objects.filter(activo=True))
        if not aerolineas or len(aeropuertos) < 2:
            self.stdout.write("No hay suficientes aerolíneas/aeropuertos para crear vuelos")
            return

        rutas = [
            ("GYE", "UIO", "45m", 89),
            ("UIO", "GYE", "45m", 89),
            ("GYE", "MIA", "4h 30m", 450),
            ("MIA", "GYE", "4h 35m", 480),
            ("UIO", "MIA", "4h 20m", 430),
            ("MIA", "UIO", "4h 25m", 460),
            ("GYE", "MCO", "3h 45m", 420),
            ("MCO", "GYE", "3h 50m", 430),
            ("GYE", "MAD", "10h 30m", 850),
            ("MAD", "GYE", "10h 45m", 870),
            ("UIO", "MAD", "10h 15m", 830),
            ("MAD", "UIO", "10h 25m", 860),
            ("GYE", "BOG", "2h 10m", 180),
            ("BOG", "GYE", "2h 15m", 190),
            ("UIO", "BOG", "2h 00m", 170),
            ("BOG", "UIO", "2h 05m", 175),
            ("GYE", "PTY", "2h 30m", 220),
            ("PTY", "GYE", "2h 35m", 230),
            ("GYE", "CUN", "3h 30m", 350),
            ("CUN", "GYE", "3h 35m", 360),
            ("UIO", "JFK", "5h 45m", 550),
            ("JFK", "UIO", "5h 50m", 560),
        ]

        aeropuertos_idx = {a.codigo_iata: a for a in aeropuertos}
        for i, (orig, dest, duracion, precio) in enumerate(rutas):
            a_o = aeropuertos_idx.get(orig)
            a_d = aeropuertos_idx.get(dest)
            if not a_o or not a_d:
                continue
            aerolinea = aerolineas[i % len(aerolineas)]
            Vuelo.objects.create(
                aerolinea=aerolinea,
                origen=a_o,
                destino=a_d,
                duracion=duracion,
                precio=precio,
                destacado=i < 6,
                disponible=True,
                imagen_url="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=400",
            )
        self.stdout.write(f"Vuelos creados: {Vuelo.objects.count()}")

    def _create_tipos(self):
        for nombre in ["Playero", "Cultural", "Aventura", "Luna de Miel", "Familiar", "Negocios", "Ecológico"]:
            TipoPaquete.objects.get_or_create(nombre=nombre)
        self.stdout.write(f"Tipos de Paquete creados: {TipoPaquete.objects.count()}")

    def _create_temporadas(self):
        for nombre in ["Alta", "Baja", "Media", "Navidad", "Verano", "Semana Santa", "Fin de Año"]:
            Temporada.objects.get_or_create(nombre=nombre)
        self.stdout.write(f"Temporadas creadas: {Temporada.objects.count()}")

    def _create_tipos_viaje(self):
        for nombre in ["Ida y Vuelta", "Solo Ida", "Multidestino"]:
            TipoViaje.objects.get_or_create(nombre=nombre)
        self.stdout.write(f"Tipos de Viaje creados: {TipoViaje.objects.count()}")

    def _create_destinos(self):
        if Destino.objects.exists():
            return
        ecuador = PaisRegion.objects.filter(codigo_iso="EC").first()
        if not ecuador:
            return
        destinos_data = [
            ("Islas Galápagos", ecuador, Ciudad.objects.filter(codigo_ciudad="GPS").first(),
             "Descubre la fauna única y paisajes volcánicos de las Islas Encantadas",
             "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=600",
             1599, True),
            ("Quito", ecuador, Ciudad.objects.filter(codigo_ciudad="UIO").first(),
             "Explora el centro histórico más grande de América, declarado Patrimonio de la Humanidad",
             "https://images.unsplash.com/photo-1589994965851-a18f38a0e0e4?w=600",
             499, True),
            ("Guayaquil", ecuador, Ciudad.objects.filter(codigo_ciudad="GYE").first(),
             "Disfruta del Malecón 2000, el Cerro Santa Ana y la vibrante vida urbana",
             "https://images.unsplash.com/photo-1552334409-4b1f0e7c8b1a?w=600",
             399, True),
            ("Cuenca", ecuador, Ciudad.objects.filter(codigo_ciudad="CUE").first(),
             "Maravíllate con la arquitectura colonial y los tejidos tradicionales",
             "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=600",
             349, False),
            ("Baños", ecuador, None,
             "Aventura, termas y cascadas en el corazón de los Andes ecuatorianos",
             "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600",
             299, True),
            ("Montañita", ecuador, None,
             "El mejor surf del Ecuador y vibrante vida nocturna playera",
             "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600",
             249, False),
            ("Amazonía (Tena)", ecuador, Ciudad.objects.filter(codigo_ciudad="TNW").first(),
             "Sumérgete en la selva amazónica y convive con comunidades indígenas",
             "https://images.unsplash.com/photo-1470071459604-4b118ecb46af?w=600",
             599, True),
        ]
        for nombre, pais, ciudad, desc, img, precio, destacado in destinos_data:
            Destino.objects.create(
                nombre=nombre, pais=pais, ciudad=ciudad,
                descripcion=desc, imagen_url=img,
                precio_desde=precio, destacado=destacado, activo=True
            )
        self.stdout.write(f"Destinos creados: {Destino.objects.count()}")

    def _create_paquetes(self):
        if PaqueteTuristico.objects.exists():
            return
        ec = PaisRegion.objects.filter(codigo_iso="EC").first()
        us = PaisRegion.objects.filter(codigo_iso="US").first()
        mx = PaisRegion.objects.filter(codigo_iso="MX").first()
        es = PaisRegion.objects.filter(codigo_iso="ES").first()
        region_sud = Region.objects.filter(nombre="sudamerica").first()
        region_norte = Region.objects.filter(nombre="norteamerica").first()
        region_caribe = Region.objects.filter(nombre="caribe").first()
        region_europa = Region.objects.filter(nombre="europa").first()
        tipo_playero = TipoPaquete.objects.filter(nombre="Playero").first()
        tipo_aventura = TipoPaquete.objects.filter(nombre="Aventura").first()
        tipo_cultural = TipoPaquete.objects.filter(nombre="Cultural").first()
        tipo_familiar = TipoPaquete.objects.filter(nombre="Familiar").first()

        paquetes = [
            {
                "titulo": "Galápagos Express",
                "subtitulo": "4 días / 3 noches",
                "region": region_sud, "pais": ec, "ciudad": Ciudad.objects.filter(codigo_ciudad="GPS").first(),
                "precio": 1299, "tipo": tipo_aventura, "noches": 3, "dias": 4,
                "salidas": "Quito y Guayaquil",
                "desc": "Descubre la magia de las Islas Galápagos en un tour exprés. Bucea con tortugas marinas, camina junto a piqueros de patas azules y navega entre formaciones volcánicas únicas.",
                "img": "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=600",
                "incluye": "Vuelo ida y vuelta, alojamiento 3 noches, desayunos, tours navegables, guía naturalista, snorkel, traslados",
                "no_incluye": "Comidas no especificadas, bebidas, propinas, tasa de ingreso a Galápagos ($200)", "destacado": True,
            },
            {
                "titulo": "Miami Beach Experience",
                "subtitulo": "5 días / 4 noches",
                "region": region_norte, "pais": us, "ciudad": None,
                "precio": 899, "tipo": tipo_playero, "noches": 4, "dias": 5,
                "salidas": "Quito y Guayaquil",
                "desc": "Vive el brillo de Miami Beach, recorre South Beach, visita el Everglades y disfruta del mejor shopping en Sawgrass Mills.",
                "img": "https://images.unsplash.com/photo-1533106497176-45ae19e68ba2?w=600",
                "incluye": "Vuelo ida y vuelta, hotel 4 noches, desayunos, tour Everglades, traslados aeropuerto-hotel",
                "no_incluye": "Comidas no especificadas, bebidas, propinas, visa americana",
                "destacado": True,
            },
            {
                "titulo": "Cancún Paraíso",
                "subtitulo": "6 días / 5 noches",
                "region": region_caribe, "pais": mx, "ciudad": None,
                "precio": 1099, "tipo": tipo_playero, "noches": 5, "dias": 6,
                "salidas": "Quito y Guayaquil",
                "desc": "Arena blanca y mar turquesa te esperan en Cancún. Visita Chichén Itzá, bucea en cenotes y disfruta de la vida nocturna.",
                "img": "https://images.unsplash.com/photo-1510097467424-192d713fd8b6?w=600",
                "incluye": "Vuelo, hotel 5 noches todo incluido, tour a Chichén Itzá, tour a Isla Mujeres, traslados",
                "no_incluye": "Propinas, gastos personales",
                "destacado": True,
            },
            {
                "titulo": "Aventura Amazónica",
                "subtitulo": "5 días / 4 noches",
                "region": region_sud, "pais": ec, "ciudad": Ciudad.objects.filter(codigo_ciudad="TNW").first(),
                "precio": 699, "tipo": tipo_aventura, "noches": 4, "dias": 5,
                "salidas": "Quito",
                "desc": "Explora la selva amazónica desde Tena. Canotaje, senderismo nocturno, visita a comunidades indígenas y observación de fauna silvestre.",
                "img": "https://images.unsplash.com/photo-1470071459604-4b118ecb46af?w=600",
                "incluye": "Vuelo Quito-Coca, alojamiento 4 noches, alimentación completa, guía nativo, tours diarios",
                "no_incluye": "Bebidas, propinas, equipo especial",
                "destacado": True,
            },
            {
                "titulo": "Europa Clásica: Madrid y Barcelona",
                "subtitulo": "8 días / 7 noches",
                "region": region_europa, "pais": es, "ciudad": None,
                "precio": 1899, "tipo": tipo_cultural, "noches": 7, "dias": 8,
                "salidas": "Quito",
                "desc": "Recorre las dos ciudades más emblemáticas de España. Museo del Prado, Park Güell, flamenco y la mejor gastronomía.",
                "img": "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=600",
                "incluye": "Vuelo ida y vuelta, hotel 7 noches, desayunos, tren Madrid-Barcelona, tour guiado, entradas a museos",
                "no_incluye": "Comidas no especificadas, visa Schengen, propinas",
                "destacado": False,
            },
            {
                "titulo": "Ruta del Sol: Montañita y Ruta Spondylus",
                "subtitulo": "4 días / 3 noches",
                "region": region_sud, "pais": ec, "ciudad": None,
                "precio": 349, "tipo": tipo_playero, "noches": 3, "dias": 4,
                "salidas": "Guayaquil",
                "desc": "Sol, playa y surf en la costa ecuatoriana. Recorre la Ruta Spondylus, disfruta del mar y la vida playera.",
                "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600",
                "incluye": "Transporte, alojamiento 3 noches, desayunos, tour Ruta Spondylus",
                "no_incluye": "Comidas no especificadas, equipo de surf",
                "destacado": False,
            },
        ]
        for p in paquetes:
            PaqueteTuristico.objects.create(
                titulo=p["titulo"],
                subtitulo=p["subtitulo"],
                region=p["region"] or region_sud,
                pais_destino=p["pais"],
                ciudad_destino=p.get("ciudad"),
                precio=p["precio"],
                tipo_paquete=p["tipo"],
                duracion_noches=p["noches"],
                duracion_dias=p["dias"],
                salidas=p["salidas"],
                descripcion_corta=p["desc"][:200],
                descripcion_extensa=p["desc"],
                imagen_url=p["img"],
                programa_incluye=p["incluye"],
                no_incluye=p["no_incluye"],
                destacado=p["destacado"],
                activo=True,
                incluye_vuelo=True,
                incluye_hotel=True,
            )
        self.stdout.write(f"Paquetes Turísticos creados: {PaqueteTuristico.objects.count()}")
