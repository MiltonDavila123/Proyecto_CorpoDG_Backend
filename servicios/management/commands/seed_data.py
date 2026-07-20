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

# PDF detallado (Google Drive) que se usa para TODOS los paquetes y destinos.
# Se normaliza automáticamente a /preview al guardar (GoogleDrivePDFMixin).
PDF_DETALLE = "https://drive.google.com/file/d/1sJjO67KTV6iesugxJacug5fGj0_VN45Y/view?usp=sharing"

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
        imagenes = {
            "caribe": "https://images.unsplash.com/photo-1580541631950-7282082b53ce?w=800",
            "sudamerica": "https://images.unsplash.com/photo-1526392060635-9d6019884377?w=800",
            "centroamerica": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=800",
            "norteamerica": "https://images.unsplash.com/photo-1485738422979-f5c462d49f74?w=800",
            "europa": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800",
            "medio_oriente": "https://images.unsplash.com/photo-1547483238-f400e65ccd56?w=800",
            "africa": "https://images.unsplash.com/photo-1489749798305-4fea3ae63d43?w=800",
            "asia": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800",
            "oceania": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800",
            "ecuador": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Panorama_quilotoa_crater_lake_ecuador.jpg/500px-Panorama_quilotoa_crater_lake_ecuador.jpg",
        }
        for orden, nombre_key in enumerate(regiones_data, start=1):
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
            Region.objects.update_or_create(
                nombre=nombre_key,
                defaults={
                    "descripcion": f"Región {nombre_display}",
                    "orden": orden,
                    "imagen_url": imagenes.get(nombre_key, ""),
                }
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
            iata = a.get("iata", "") or ""
            aerolinea, created = Aerolinea.objects.get_or_create(
                nombre=a.get("name", ""),
                defaults={
                    "codigo_iata": iata,
                    "codigo_icao": a.get("icao", ""),
                    "pais_origen": a.get("country", ""),
                    "logo_url": a.get("logo_url", ""),
                }
            )
            if not created and iata and not aerolinea.codigo_iata:
                aerolinea.codigo_iata = iata
                aerolinea.save()
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
            ("UIO", "LIM", "2h 00m", 210),
            ("LIM", "UIO", "2h 05m", 220),
            ("GYE", "LIM", "1h 50m", 200),
            ("LIM", "GYE", "1h 55m", 205),
            ("UIO", "CUZ", "3h 30m", 340),
            ("CUZ", "UIO", "3h 35m", 350),
            ("GYE", "SDQ", "4h 10m", 470),
            ("SDQ", "GYE", "4h 15m", 480),
            ("UIO", "CTG", "2h 40m", 260),
            ("CTG", "UIO", "2h 45m", 270),
            ("GYE", "BCN", "11h 20m", 910),
            ("BCN", "GYE", "11h 30m", 930),
            ("UIO", "GIG", "6h 10m", 640),
            ("GIG", "UIO", "6h 20m", 660),
        ]

        aeropuertos_idx = {a.codigo_iata: a for a in aeropuertos}
        for i, (orig, dest, duracion, precio) in enumerate(rutas):
            a_o = aeropuertos_idx.get(orig)
            a_d = aeropuertos_idx.get(dest)
            if not a_o or not a_d:
                continue
            aerolinea = aerolineas[i % len(aerolineas)]
            Vuelo.objects.get_or_create(
                aerolinea=aerolinea,
                origen=a_o,
                destino=a_d,
                defaults={
                    "duracion": duracion,
                    "precio": precio,
                    "destacado": i < 6,
                    "disponible": True,
                    "imagen_url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=400",
                },
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
        Destino.objects.all().delete()
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
            ("Cotopaxi", ecuador, None,
             "Escala uno de los volcanes activos más altos del mundo entre páramos andinos",
             "https://images.unsplash.com/photo-1531761535209-180857e963b9?w=600",
             449, True),
            ("Mitad del Mundo", ecuador, Ciudad.objects.filter(codigo_ciudad="UIO").first(),
             "Párate sobre la línea ecuatorial en el monumento de la Latitud Cero",
             "https://images.unsplash.com/photo-1526392060635-9d6019884377?w=600",
             199, True),
            ("Cuyabeno", ecuador, None,
             "Reserva de vida silvestre con delfines rosados, lagunas y biodiversidad única",
             "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?w=600",
             699, False),
        ]
        # Destinos internacionales (se crean solo si el país existe)
        internacionales = [
            ("PE", "Machu Picchu", "Descubre la ciudadela inca perdida entre montañas y neblina",
             "https://images.unsplash.com/photo-1526392060635-9d6019884377?w=600", 1290, True),
            ("MX", "Cancún", "Playas de arena blanca y mar turquesa en el Caribe mexicano",
             "https://images.unsplash.com/photo-1510097467424-192d713fd8b2?w=600", 1099, True),
            ("CO", "Cartagena", "Ciudad amurallada colonial frente al mar Caribe",
             "https://images.unsplash.com/photo-1583531352515-8b94f7c3f0d9?w=600", 780, False),
            ("ES", "Barcelona", "Arquitectura de Gaudí, playa y la mejor gastronomía mediterránea",
             "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=600", 1650, True),
            ("BR", "Río de Janeiro", "El Cristo Redentor, Copacabana y la alegría carioca",
             "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=600", 990, False),
        ]
        for iso, nombre, desc, img, precio, destacado in internacionales:
            pais = PaisRegion.objects.filter(codigo_iso=iso).first()
            if pais:
                destinos_data.append((nombre, pais, None, desc, img, precio, destacado))

        for nombre, pais, ciudad, desc, img, precio, destacado in destinos_data:
            Destino.objects.create(
                nombre=nombre, pais=pais, ciudad=ciudad,
                descripcion=desc, imagen_url=img,
                precio_desde=precio, destacado=destacado, activo=True,
                pdf_url=PDF_DETALLE,
            )
        self.stdout.write(f"Destinos creados: {Destino.objects.count()}")

    def _create_paquetes(self):
        PaqueteTuristico.objects.all().delete()
        ec = PaisRegion.objects.filter(codigo_iso="EC").first()
        us = PaisRegion.objects.filter(codigo_iso="US").first()
        mx = PaisRegion.objects.filter(codigo_iso="MX").first()
        es = PaisRegion.objects.filter(codigo_iso="ES").first()
        pe = PaisRegion.objects.filter(codigo_iso="PE").first()
        co = PaisRegion.objects.filter(codigo_iso="CO").first()
        do = PaisRegion.objects.filter(codigo_iso="DO").first()
        region_sud = Region.objects.filter(nombre="sudamerica").first()
        region_norte = Region.objects.filter(nombre="norteamerica").first()
        region_caribe = Region.objects.filter(nombre="caribe").first()
        region_europa = Region.objects.filter(nombre="europa").first()
        region_ecuador = Region.objects.filter(nombre="ecuador").first()
        tipo_playero = TipoPaquete.objects.filter(nombre="Playero").first()
        tipo_aventura = TipoPaquete.objects.filter(nombre="Aventura").first()
        tipo_cultural = TipoPaquete.objects.filter(nombre="Cultural").first()
        tipo_familiar = TipoPaquete.objects.filter(nombre="Familiar").first()
        tipo_luna_miel = TipoPaquete.objects.filter(nombre="Luna de Miel").first()
        tipo_ecologico = TipoPaquete.objects.filter(nombre="Ecológico").first()

        aerolinea_latam = (Aerolinea.objects.filter(codigo_iata="LA").first()
            or Aerolinea.objects.filter(nombre__icontains="LATAM").first())
        aerolinea_avianca = (Aerolinea.objects.filter(codigo_iata="AV").first()
            or Aerolinea.objects.filter(nombre__icontains="Avianca").first())
        aerolinea_american = (Aerolinea.objects.filter(codigo_iata="AA").first()
            or Aerolinea.objects.filter(nombre__icontains="American Airlines").first())
        aerolinea_iberia = (Aerolinea.objects.filter(codigo_iata="IB").first()
            or Aerolinea.objects.filter(nombre__icontains="Iberia").first())

        paquetes = [
            {
                "titulo": "Galápagos Express",
                "subtitulo": "4 días / 3 noches",
                "titulo_detalle": "GALÁPAGOS EXPRESS — 4 DÍAS / 3 NOCHES",
                "region": region_sud, "pais": ec,
                "ciudad": Ciudad.objects.filter(codigo_ciudad="GPS").first(),
                "aerolinea": aerolinea_latam,
                "precio": 1299, "tipo": tipo_aventura, "noches": 3, "dias": 4,
                "salidas": "Quito y Guayaquil",
                "fecha_salidas_texto": "Enero a Diciembre 2026",
                "desc_corta": "Descubre la magia de las Islas Galápagos en un tour exprés de 4 días.",
                "desc_extensa": "Embárcate en una aventura inolvidable a las Islas Galápagos, el archipiélago volcánico que inspiró la teoría de la evolución de Darwin. Durante 4 días explorarás playas de arena blanca, bucearás con tortugas marinas, caminarás junto a piqueros de patas azules y navegarás entre formaciones volcánicas únicas en el mundo. Este tour incluye visitas guiadas a la Estación Científica Charles Darwin, la Bahía Tortuga y la Lobería, con acompañamiento de un guía naturalista certificado.",
                "img": "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=600",
                "incluye": "Vuelo ida y vuelta Quito/Galápagos\nAlojamiento 3 noches en hotel turístico\nDesayunos incluidos\nTours navegables a islas cercanas\nGuía naturalista bilingüe\nEquipo de snorkel\nTraslados aeropuerto-hotel-aeropuerto\nSeguro de viaje básico",
                "no_incluye": "Comidas no especificadas\nBebidas alcohólicas y gaseosas\nPropinas para guías y personal\nTasa de ingreso al Parque Nacional Galápagos ($200 por persona)\nTarjeta de Control Migratorio ($20 por persona)\nGastos personales y compras",
                "como_reservar": "Para reservar este paquete, contáctanos a través del formulario de contacto en nuestra página web o escríbenos directamente a nuestro WhatsApp. Uno de nuestros asesores te guiará en el proceso de reserva y te confirmará la disponibilidad en 24 horas.",
                "importante": "Los precios están sujetos a disponibilidad y pueden variar según la temporada. Se requiere pasaporte vigente con mínimo 6 meses de validez. El ingreso a Galápagos tiene un costo adicional de $200 por concepto de tasa de conservación. Recomendamos reservar con al menos 15 días de anticipación.",
                "requisitos_viaje": "Pasaporte vigente (mínimo 6 meses)\nTarjeta de Control Migratorio ($20)\nTasa de ingreso a Galápagos ($200)\nSeguro de viaje recomendado\nNo se requiere visa para ciudadanos ecuatorianos",
                "formas_pago": "Transferencia bancaria\nDepósito en cuenta\nTarjetas de crédito (3% de recargo)\nEfectivo en nuestras oficinas\nPago a través de Stripe (próximamente)",
                "politica_cancelacion": "Cancelación con hasta 30 días de anticipación: reembolso del 90%\nCancelación entre 15 y 29 días: reembolso del 50%\nCancelación con menos de 15 días: no aplica reembolso\nCargos bancarios no reembolsables",
                "lugares_destacados": "Estación Científica Charles Darwin,Bahía Tortuga,La Lobería,Isla Santa Fe,Túnel de Lava,Tortuga Bay",
                "documentos_requeridos": "Pasaporte o cédula de identidad vigente",
                "temperatura": "24°C - 30°C",
                "precio_aplica_desde": "2026-01-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": True,
            },
            {
                "titulo": "Miami Beach Experience",
                "subtitulo": "5 días / 4 noches",
                "titulo_detalle": "MIAMI BEACH EXPERIENCE — 5 DÍAS / 4 NOCHES",
                "region": region_norte, "pais": us, "ciudad": None,
                "aerolinea": aerolinea_american,
                "precio": 899, "tipo": tipo_playero, "noches": 4, "dias": 5,
                "salidas": "Quito y Guayaquil",
                "fecha_salidas_texto": "Febrero a Noviembre 2026",
                "desc_corta": "Vive el brillo de Miami Beach con playas, compras y naturaleza.",
                "desc_extensa": "Miami te espera con sus playas de arena blanca, su vibrante vida nocturna y una mezcla única de culturas. Este paquete de 5 días incluye visitas al icónico South Beach, un tour por los Everglades donde verás caimanes en su hábitat natural, y una tarde de compras en Sawgrass Mills, el centro comercial más grande de Florida. Además, recorrerás el colorido barrio de Little Havana y disfrutarás de la auténtica cocina cubana.",
                "img": "https://images.unsplash.com/photo-1533106497176-45ae19e68ba2?w=600",
                "incluye": "Vuelo ida y vuelta Quito/Miami\nHotel 4 noches en Miami Beach\nDesayunos incluidos\nTour por los Everglades en airboat\nTarde de compras en Sawgrass Mills\nRecorrido por South Beach y Little Havana\nTraslados aeropuerto-hotel-aeropuerto\nSeguro de viaje básico",
                "no_incluye": "Comidas no especificadas\nBebidas alcohólicas\nPropinas para guías\nVisa americana (si aplica)\nGastos personales y compras\nTasa de salida del aeropuerto",
                "como_reservar": "Para reservar este paquete, completa el formulario de contacto en nuestra página web o comunícate con nosotros vía WhatsApp. Te confirmaremos la disponibilidad en un máximo de 24 horas y te guiaremos en el proceso de pago.",
                "importante": "Los precios están sujetos a disponibilidad. Se requiere pasaporte vigente y visa americana vigente para ciudadanos ecuatorianos. Recomendamos gestionar la visa con al menos 2 meses de anticipación. Los menores de edad deben viajar con autorización notariada si no viajan con ambos padres.",
                "requisitos_viaje": "Pasaporte vigente (mínimo 6 meses)\nVisa americana vigente (B1/B2)\nSeguro de viaje recomendado\nAutorización notariada para menores\nESTA si aplica",
                "formas_pago": "Transferencia bancaria\nDepósito en cuenta\nTarjetas de crédito (3% recargo)\nPago en efectivo en oficinas",
                "politica_cancelacion": "Cancelación con hasta 30 días: reembolso del 90%\nCancelación entre 15 y 29 días: reembolso del 50%\nCancelación con menos de 15 días: no reembolso\nGastos de visa no reembolsables",
                "lugares_destacados": "South Beach,Everglades National Park,Sawgrass Mills,Little Havana,Wynwood Walls,Bayside Marketplace",
                "documentos_requeridos": "Pasaporte vigente y visa americana",
                "temperatura": "24°C - 32°C",
                "precio_aplica_desde": "2026-02-01",
                "precio_aplica_hasta": "2026-11-30",
                "destacado": True,
            },
            {
                "titulo": "Cancún Paraíso",
                "subtitulo": "6 días / 5 noches",
                "titulo_detalle": "CANCÚN PARAÍSO — 6 DÍAS / 5 NOCHES",
                "region": region_caribe, "pais": mx, "ciudad": None,
                "aerolinea": aerolinea_avianca,
                "precio": 1099, "tipo": tipo_playero, "noches": 5, "dias": 6,
                "salidas": "Quito y Guayaquil",
                "fecha_salidas_texto": "Enero a Diciembre 2026",
                "desc_corta": "Arena blanca y mar turquesa te esperan en Cancún con todo incluido.",
                "desc_extensa": "Cancún es el destino playero por excelencia del Caribe mexicano. Este paquete todo incluido de 6 días te permite disfrutar de las mejores playas de arena blanca y mar turquesa, explorar las ruinas mayas de Chichén Itzá (una de las 7 maravillas del mundo moderno), bucear en cenotes cristalinos y navegar a la paradisíaca Isla Mujeres. Incluye hotel 5 estrellas con régimen todo incluido y actividades diarias.",
                "img": "https://images.unsplash.com/photo-1504214208698-ea1916a2195a?w=600",
                "incluye": "Vuelo ida y vuelta Quito/Cancún\nHotel 5 noches todo incluido\nTour a Chichén Itzá con guía\nTour a Isla Mujeres\nBuceo en cenote\nTraslados aeropuerto-hotel-aeropuerto\nSeguro de viaje básico\nImpuestos hoteleros",
                "no_incluye": "Propinas para guías\nGastos personales\nFotos y recuerdos\nBebidas premium en hotel\nLlamadas telefónicas\nLavandería",
                "como_reservar": "Puedes reservar este paquete a través de nuestro formulario de contacto en la página web, o escribiéndonos directamente a nuestro WhatsApp. Un asesor especializado te atenderá y coordinará todos los detalles de tu viaje.",
                "importante": "Precios sujetos a disponibilidad y temporada. Se requiere pasaporte vigente. Los ciudadanos ecuatorianos no necesitan visa para estancias turísticas menores a 180 días en México. Se recomienda reservar con 20 días de anticipación para mejores tarifas.",
                "requisitos_viaje": "Pasaporte vigente (mínimo 6 meses)\nNo requiere visa para ecuatorianos (estancia < 180 días)\nSeguro de viaje recomendado\nFormulario de turista (FMM)",
                "formas_pago": "Transferencia bancaria\nDepósito en cuenta\nTarjetas de crédito (3% recargo)\nPago en oficinas\nPayPal",
                "politica_cancelacion": "Cancelación con hasta 30 días: reembolso del 85%\nCancelación entre 15 y 29 días: reembolso del 50%\nCancelación con menos de 15 días: no reembolso",
                "lugares_destacados": "Chichén Itzá,Isla Mujeres,Cenote Ik Kil,Playa Delfines,Tulum,Xcaret",
                "documentos_requeridos": "Pasaporte vigente",
                "temperatura": "26°C - 35°C",
                "precio_aplica_desde": "2026-01-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": True,
            },
            {
                "titulo": "Aventura Amazónica",
                "subtitulo": "5 días / 4 noches",
                "titulo_detalle": "AVENTURA AMAZÓNICA — 5 DÍAS / 4 NOCHES",
                "region": region_sud, "pais": ec,
                "ciudad": Ciudad.objects.filter(codigo_ciudad="TNW").first(),
                "aerolinea": aerolinea_latam,
                "precio": 699, "tipo": tipo_aventura, "noches": 4, "dias": 5,
                "salidas": "Quito",
                "fecha_salidas_texto": "Marzo a Diciembre 2026",
                "desc_corta": "Explora la selva amazónica ecuatoriana desde Tena.",
                "desc_extensa": "Sumérgete en la selva amazónica ecuatoriana, uno de los lugares con mayor biodiversidad del planeta. Este paquete de 5 días te lleva a Tena, la puerta de entrada a la Amazonía. Incluye canotaje por ríos cristalinos, senderismo nocturno para observar fauna, visitas a comunidades indígenas donde aprenderás sobre sus tradiciones y medicina ancestral, y observación de aves exóticas. Una experiencia transformadora en contacto con la naturaleza más pura.",
                "img": "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=600",
                "incluye": "Vuelo Quito-Coca ida y vuelta\nAlojamiento 4 noches en lodge amazónico\nAlimentación completa durante la estadía\nGuía nativo bilingüe\nCanotaje por el río Napo\nSenderismo diurno y nocturno\nVisita a comunidad indígena\nObservación de aves y fauna\nEquipo de camping básico",
                "no_incluye": "Bebidas alcohólicas\nPropinas para guías\nEquipo especial de fotografía\nRopa impermeable (se puede alquilar)\nGastos personales",
                "como_reservar": "Reserva este paquete a través de nuestro formulario de contacto. Un asesor especializado en turismo de aventura te contactará para coordinar los detalles logísticos y de equipo necesario.",
                "importante": "Este paquete requiere buena condición física. No recomendado para personas con movilidad reducida. Se recomienda llevar ropa ligera, impermeable, repelente de insectos y linterna. Las actividades están sujetas a condiciones climáticas.",
                "requisitos_viaje": "Cédula de identidad o pasaporte vigente\nSeguro de viaje con cobertura de rescate (recomendado)\nVacuna contra la fiebre amarilla (recomendada)",
                "formas_pago": "Transferencia bancaria\nDepósito en cuenta\nTarjetas de crédito (3% recargo)\nEfectivo en oficinas",
                "politica_cancelacion": "Cancelación con hasta 15 días: reembolso del 80%\nCancelación con menos de 15 días: no reembolso",
                "lugares_destacados": "Río Napo,Comunidad Kichwa Añangu,Misahuallí,Cuevas de Jumandy,Parque Nacional Sumaco,Laguna de Limoncocha",
                "documentos_requeridos": "Cédula o pasaporte vigente",
                "temperatura": "23°C - 30°C",
                "precio_aplica_desde": "2026-03-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": True,
            },
            {
                "titulo": "Europa Clásica: Madrid y Barcelona",
                "subtitulo": "8 días / 7 noches",
                "titulo_detalle": "EUROPA CLÁSICA — MADRID Y BARCELONA — 8 DÍAS / 7 NOCHES",
                "region": region_europa, "pais": es, "ciudad": None,
                "aerolinea": aerolinea_iberia,
                "precio": 1899, "tipo": tipo_cultural, "noches": 7, "dias": 8,
                "salidas": "Quito",
                "fecha_salidas_texto": "Mayo a Septiembre 2026",
                "desc_corta": "Recorre las dos ciudades más emblemáticas de España.",
                "desc_extensa": "Descubre la riqueza cultural de España en este completo paquete de 8 días que recorre Madrid y Barcelona. En Madrid visitarás el Museo del Prado, el Palacio Real y la Plaza Mayor. Viajarás en tren AVE a Barcelona donde te esperan el Park Güell, la Sagrada Familia y las Ramblas. Disfrutarás de la mejor gastronomía española y vivirás la pasión del flamenco en vivo.",
                "img": "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=600",
                "incluye": "Vuelo ida y vuelta Quito/Madrid\nHotel 4 noches en Madrid\nTren AVE Madrid-Barcelona\nHotel 3 noches en Barcelona\nDesayunos incluidos\nTour guiado por Madrid\nTour guiado por Barcelona\nEntradas al Museo del Prado\nEntradas a Sagrada Familia\nEntradas Park Güell\nEspectáculo de flamenco\nSeguro de viaje",
                "no_incluye": "Comidas no especificadas\nVisa Schengen\nPropinas para guías\nGastos personales\nCompras\nTransporte municipal",
                "como_reservar": "Para reservar, contáctanos mediante el formulario de nuestra web. Te asignaremos un asesor especializado en viajes internacionales que coordinará todos los detalles, incluyendo la gestión de la visa Schengen si es necesaria.",
                "importante": "Se requiere pasaporte vigente y visa Schengen para ciudadanos ecuatorianos. Recomendamos iniciar el trámite de visa con al menos 3 meses de anticipación. Los precios no incluyen tasas aeroportuarias internacionales. Se recomienda reservar con 45 días de anticipación.",
                "requisitos_viaje": "Pasaporte vigente (mínimo 6 meses)\nVisa Schengen (si aplica)\nSeguro de viaje con cobertura internacional\nReserva de hotel confirmada",
                "formas_pago": "Transferencia bancaria\nDepósito en cuenta\nTarjetas de crédito (3% recargo)\nPago fraccionado disponible",
                "politica_cancelacion": "Cancelación con hasta 45 días: reembolso del 90%\nCancelación entre 30 y 44 días: reembolso del 60%\nCancelación entre 15 y 29 días: reembolso del 30%\nCancelación con menos de 15 días: no reembolso",
                "lugares_destacados": "Museo del Prado,Palacio Real,Plaza Mayor,Sagrada Familia,Park Güell,Las Ramblas,Camp Nou",
                "documentos_requeridos": "Pasaporte vigente y visa Schengen",
                "temperatura": "18°C - 32°C",
                "precio_aplica_desde": "2026-05-01",
                "precio_aplica_hasta": "2026-09-30",
                "destacado": False,
            },
            {
                "titulo": "Ruta del Sol: Montañita",
                "subtitulo": "4 días / 3 noches",
                "titulo_detalle": "RUTA DEL SOL — MONTAÑITA Y RUTA SPONDYLUS — 4 DÍAS / 3 NOCHES",
                "region": region_sud, "pais": ec, "ciudad": None,
                "aerolinea": None,
                "precio": 349, "tipo": tipo_playero, "noches": 3, "dias": 4,
                "salidas": "Guayaquil",
                "fecha_salidas_texto": "Todo el año 2026",
                "desc_corta": "Sol, playa y surf en la costa ecuatoriana.",
                "desc_extensa": "Disfruta de 4 días de sol, playa y aventura en la costa ecuatoriana. Montañita es el destino surfista por excelencia del Ecuador, famosa por sus olas perfectas y su vibrante vida playera. Recorre la impresionante Ruta Spondylus, visita los acantilados de Los Frailes, relájate en las playas de Olón y ayunate del mejor marisco ecuatoriano. Ideal para quienes buscan desconexión y naturaleza.",
                "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600",
                "incluye": "Transporte Guayaquil-Montañita-Guayaquil\nAlojamiento 3 noches frente al mar\nDesayunos incluidos\nTour por la Ruta Spondylus\nVisita a la Playa Los Frailes\nClase de surf básica (1 hora)\nSeguro de viaje básico",
                "no_incluye": "Comidas no especificadas\nEquipo de surf especializado\nBebidas alcohólicas\nPropinas\nGastos personales",
                "como_reservar": "Reserva fácilmente a través de nuestro formulario de contacto web o WhatsApp. Te confirmaremos la disponibilidad en cuestión de horas.",
                "importante": "Paquete económico ideal para escapadas de fin de semana largo. No incluye vuelos porque la salida es desde Guayaquil por vía terrestre (2.5 horas de trayecto). Se recomienda llevar bloqueador solar biodegradable, repelente y ropa ligera.",
                "requisitos_viaje": "Cédula de identidad vigente\nSeguro de viaje opcional",
                "formas_pago": "Transferencia bancaria\nDepósito en cuenta\nEfectivo en oficinas\nTarjetas de crédito (3% recargo)",
                "politica_cancelacion": "Cancelación con hasta 7 días: reembolso del 80%\nCancelación con menos de 7 días: no reembolso",
                "lugares_destacados": "Montañita,Playa Los Frailes,Olón,Ruta Spondylus,Ayangue,Valdivia",
                "documentos_requeridos": "Cédula de identidad vigente",
                "temperatura": "25°C - 32°C",
                "precio_aplica_desde": "2026-01-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": False,
            },
            {
                "titulo": "Expedición Mitad del Mundo",
                "subtitulo": "7 días / 6 noches",
                "titulo_detalle": "EXPEDICIÓN MITAD DEL MUNDO — DESCUBRE LOS ANDES Y LA MAGIA AMAZÓNICA",
                "region": region_ecuador or region_sud, "pais": ec,
                "ciudad": Ciudad.objects.filter(codigo_ciudad="UIO").first(),
                "aerolinea": aerolinea_latam,
                "precio": 1450, "tipo": tipo_aventura, "noches": 6, "dias": 7,
                "salidas": "Quito",
                "fecha_salidas_texto": "Enero a Diciembre 2026",
                "desc_corta": "Descubre los Andes y la magia amazónica: Quito, Cotopaxi y la selva de Cuyabeno en 7 días.",
                "desc_extensa": "Embárcate en una aventura sin precedentes diseñada para los viajeros más exigentes. Desde las majestuosas cumbres andinas hasta la profundidad inexplorada de la selva amazónica, esta experiencia exclusiva combina confort, cultura y naturaleza pura.\n\nDía 1: Llegada a la Capital de las Nubes. Recepción VIP en el Aeropuerto Internacional Mariscal Sucre (Quito) y traslado en vehículo privado a su hotel boutique en el centro histórico.\nDía 2: Tesoros Coloniales y la Latitud Cero. Exploración del centro histórico mejor conservado de América, la Basílica del Voto Nacional y la Iglesia de la Compañía de Jesús, y visita al complejo Ciudad Mitad del Mundo.\nDía 3: La Majestuosidad del Cotopaxi. Ascenso al Parque Nacional Cotopaxi, caminata por los páramos andinos hasta el refugio José Rivas (4.864 msnm) y recorrido por la laguna de Limpiopungo.\nDía 4: Inmersión en la Selva - Cuyabeno. Vuelo a Lago Agrio y traslado fluvial en canoa hacia el Eco-Lodge, con observación de monos, tucanes y orquídeas salvajes.\nDía 5: La Laguna Grande y Delfines Rosados. Navegación a la Laguna Grande para el atardecer y avistamiento de delfines rosados, más caminata nocturna de fauna.\nDía 6: Cultura Indígena y Naturaleza. Visita a una comunidad Siona, elaboración tradicional del pan de yuca (casabe) y pesca de pirañas.\nDía 7: Despedida y Retorno. Observación de aves al amanecer, desayuno amazónico y retorno a Quito.",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Mitad_del_Mundo%2C_Quito%2C_Ecuador%2C_2015-07-22%2C_DD_03.JPG/500px-Mitad_del_Mundo%2C_Quito%2C_Ecuador%2C_2015-07-22%2C_DD_03.JPG",
                "incluye": "Alojamiento en Hoteles Boutique (Quito) y Eco-Lodge (Cuyabeno)\nVuelos internos (Quito - Lago Agrio - Quito)\nTransporte privado para todas las excursiones\nAlimentación completa en la selva (Pensión completa)\nGuías naturalistas bilingües y equipo de excursión",
                "no_incluye": "Vuelos internacionales y tasas aeroportuarias\nCenas y almuerzos en Quito (Días 1, 2 y 3)\nGastos personales, bebidas alcohólicas y propinas\nSeguro médico y de viaje (Obligatorio)",
                "como_reservar": "Escríbenos a reservas@trip593.com o a través del formulario de contacto de nuestra web. Un asesor confirmará la disponibilidad en 24 horas.",
                "importante": "El Día 3 incluye una caminata de altura hasta los 4.864 msnm; se recomienda buena condición física y aclimatación. El seguro médico y de viaje es obligatorio. Precios sujetos a disponibilidad y temporada.",
                "requisitos_viaje": "Pasaporte vigente (mínimo 6 meses)\nSeguro médico y de viaje obligatorio\nVacuna contra la fiebre amarilla (recomendada para la Amazonía)\nRopa de abrigo para el páramo y ropa ligera para la selva",
                "formas_pago": "Transferencia bancaria\nDepósito en cuenta\nTarjetas de crédito (3% de recargo)\nPago a través de Stripe",
                "politica_cancelacion": "Cancelación con hasta 30 días: reembolso del 90%\nCancelación entre 15 y 29 días: reembolso del 50%\nCancelación con menos de 15 días: no aplica reembolso",
                "lugares_destacados": "Centro Histórico de Quito,Mitad del Mundo,Parque Nacional Cotopaxi,Laguna de Limpiopungo,Reserva Cuyabeno,Laguna Grande",
                "documentos_requeridos": "Pasaporte vigente",
                "temperatura": "8°C (páramo) - 32°C (selva)",
                "precio_aplica_desde": "2026-01-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": True,
            },
            {
                "titulo": "Perú Mágico: Cusco y Machu Picchu",
                "subtitulo": "6 días / 5 noches",
                "titulo_detalle": "PERÚ MÁGICO — CUSCO Y MACHU PICCHU — 6 DÍAS / 5 NOCHES",
                "region": region_sud, "pais": pe or ec, "ciudad": None,
                "aerolinea": aerolinea_latam,
                "precio": 1390, "tipo": tipo_cultural, "noches": 5, "dias": 6,
                "salidas": "Quito y Guayaquil",
                "fecha_salidas_texto": "Enero a Diciembre 2026",
                "desc_corta": "Recorre el Valle Sagrado de los Incas y la ciudadela de Machu Picchu.",
                "desc_extensa": "Viaja al corazón del imperio Inca en este paquete de 6 días. Explora la ciudad de Cusco, capital arqueológica de América, recorre el Valle Sagrado con sus mercados y fortalezas, y culmina con la visita a la mítica ciudadela de Machu Picchu, una de las 7 maravillas del mundo moderno. Incluye tren panorámico y guías especializados en cultura andina.",
                "img": "https://images.unsplash.com/photo-1526392060635-9d6019884377?w=600",
                "incluye": "Vuelo ida y vuelta Quito/Cusco\nHotel 5 noches en Cusco\nTren panorámico a Aguas Calientes\nEntrada y tour guiado a Machu Picchu\nTour por el Valle Sagrado\nDesayunos incluidos\nTraslados aeropuerto-hotel-aeropuerto",
                "no_incluye": "Almuerzos y cenas\nBebidas\nPropinas\nGastos personales\nBoleto de subida al Huayna Picchu (opcional)",
                "como_reservar": "Contáctanos por el formulario web o WhatsApp y un asesor coordinará tu reserva y la compra anticipada de entradas a Machu Picchu.",
                "importante": "Las entradas a Machu Picchu tienen cupo limitado; se recomienda reservar con 30 días de anticipación. Cusco está a 3.400 msnm: se recomienda aclimatación por el soroche (mal de altura).",
                "requisitos_viaje": "Pasaporte o cédula vigente\nSeguro de viaje recomendado\nNo se requiere visa para ecuatorianos",
                "formas_pago": "Transferencia bancaria\nTarjetas de crédito (3% recargo)\nPago a través de Stripe",
                "politica_cancelacion": "Cancelación con hasta 30 días: reembolso del 85%\nCancelación entre 15 y 29 días: reembolso del 40%\nEntradas a Machu Picchu no reembolsables",
                "lugares_destacados": "Machu Picchu,Cusco,Valle Sagrado,Ollantaytambo,Sacsayhuamán,Pisac",
                "documentos_requeridos": "Pasaporte o cédula vigente",
                "temperatura": "10°C - 22°C",
                "precio_aplica_desde": "2026-01-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": True,
            },
            {
                "titulo": "Punta Cana All Inclusive",
                "subtitulo": "5 días / 4 noches",
                "titulo_detalle": "PUNTA CANA ALL INCLUSIVE — 5 DÍAS / 4 NOCHES",
                "region": region_caribe, "pais": do or ec, "ciudad": None,
                "aerolinea": aerolinea_avianca,
                "precio": 1250, "tipo": tipo_playero, "noches": 4, "dias": 5,
                "salidas": "Quito y Guayaquil",
                "fecha_salidas_texto": "Todo el año 2026",
                "desc_corta": "Resort todo incluido frente a las mejores playas del Caribe dominicano.",
                "desc_extensa": "Relájate en Punta Cana, el paraíso caribeño de República Dominicana. Este paquete todo incluido de 5 días te aloja en un resort frente al mar con playas de arena blanca, palmeras y aguas cristalinas. Disfruta de piscinas, deportes acuáticos, gastronomía internacional ilimitada y espectáculos nocturnos. Ideal para parejas y familias que buscan descanso total.",
                "img": "https://images.unsplash.com/photo-1510097467424-192d713fd8b2?w=600",
                "incluye": "Vuelo ida y vuelta\nResort 4 noches todo incluido\nComidas y bebidas ilimitadas\nDeportes acuáticos no motorizados\nEspectáculos nocturnos\nTraslados aeropuerto-hotel-aeropuerto\nSeguro de viaje básico",
                "no_incluye": "Excursiones opcionales\nSpa y masajes\nDeportes acuáticos motorizados\nPropinas\nGastos personales",
                "como_reservar": "Reserva por el formulario de contacto o WhatsApp; confirmamos disponibilidad en 24 horas.",
                "importante": "Los ciudadanos ecuatorianos no requieren visa para estancias turísticas en República Dominicana. Se paga una tarjeta de turista incluida en la mayoría de tarifas aéreas.",
                "requisitos_viaje": "Pasaporte vigente (mínimo 6 meses)\nTarjeta de turista\nSeguro de viaje recomendado",
                "formas_pago": "Transferencia bancaria\nTarjetas de crédito (3% recargo)\nPago a través de Stripe",
                "politica_cancelacion": "Cancelación con hasta 30 días: reembolso del 85%\nCancelación entre 15 y 29 días: reembolso del 50%\nCancelación con menos de 15 días: no reembolso",
                "lugares_destacados": "Playa Bávaro,Isla Saona,Hoyo Azul,Cap Cana,Altos de Chavón,Marina Cap Cana",
                "documentos_requeridos": "Pasaporte vigente",
                "temperatura": "26°C - 31°C",
                "precio_aplica_desde": "2026-01-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": True,
            },
            {
                "titulo": "Colombia Colonial: Cartagena",
                "subtitulo": "4 días / 3 noches",
                "titulo_detalle": "COLOMBIA COLONIAL — CARTAGENA DE INDIAS — 4 DÍAS / 3 NOCHES",
                "region": region_sud, "pais": co or ec, "ciudad": None,
                "aerolinea": aerolinea_avianca,
                "precio": 780, "tipo": tipo_cultural, "noches": 3, "dias": 4,
                "salidas": "Quito y Guayaquil",
                "fecha_salidas_texto": "Todo el año 2026",
                "desc_corta": "La ciudad amurallada, el Caribe y la historia colonial de Colombia.",
                "desc_extensa": "Cartagena de Indias combina historia, color y playa. En este paquete de 4 días recorrerás la ciudad amurallada declarada Patrimonio de la Humanidad, el imponente Castillo de San Felipe, el bohemio barrio de Getsemaní y navegarás a las paradisíacas Islas del Rosario. Una escapada perfecta al Caribe colombiano.",
                "img": "https://images.unsplash.com/photo-1583531352515-8b94f7c3f0d9?w=600",
                "incluye": "Vuelo ida y vuelta\nHotel 3 noches en el centro histórico\nDesayunos incluidos\nCity tour por la ciudad amurallada\nTour a las Islas del Rosario\nTraslados aeropuerto-hotel-aeropuerto",
                "no_incluye": "Almuerzos y cenas\nBebidas\nPropinas\nImpuesto de las islas\nGastos personales",
                "como_reservar": "Escríbenos por el formulario o WhatsApp y coordinamos tu reserva en 24 horas.",
                "importante": "Los ciudadanos ecuatorianos no requieren visa para Colombia. Las excursiones a las islas dependen de las condiciones del mar.",
                "requisitos_viaje": "Cédula o pasaporte vigente\nSeguro de viaje recomendado",
                "formas_pago": "Transferencia bancaria\nTarjetas de crédito (3% recargo)\nPago a través de Stripe",
                "politica_cancelacion": "Cancelación con hasta 20 días: reembolso del 80%\nCancelación con menos de 20 días: reembolso del 40%",
                "lugares_destacados": "Ciudad Amurallada,Castillo de San Felipe,Getsemaní,Islas del Rosario,Torre del Reloj,Bocagrande",
                "documentos_requeridos": "Cédula o pasaporte vigente",
                "temperatura": "27°C - 33°C",
                "precio_aplica_desde": "2026-01-01",
                "precio_aplica_hasta": "2026-12-31",
                "destacado": False,
            },
        ]
        for p in paquetes:
            PaqueteTuristico.objects.create(
                titulo=p["titulo"],
                subtitulo=p["subtitulo"],
                titulo_detalle=p.get("titulo_detalle", ""),
                region=p["region"] or region_sud,
                pais_destino=p["pais"],
                ciudad_destino=p.get("ciudad"),
                aerolinea=p.get("aerolinea"),
                precio=p["precio"],
                tipo_paquete=p["tipo"],
                duracion_noches=p["noches"],
                duracion_dias=p["dias"],
                salidas=p["salidas"],
                fecha_salidas_texto=p.get("fecha_salidas_texto", ""),
                descripcion_corta=p["desc_corta"],
                descripcion_extensa=p["desc_extensa"],
                imagen_url=p["img"],
                programa_incluye=p["incluye"],
                no_incluye=p["no_incluye"],
                como_reservar=p.get("como_reservar", ""),
                importante=p.get("importante", ""),
                requisitos_viaje=p.get("requisitos_viaje", ""),
                formas_pago=p.get("formas_pago", ""),
                politica_cancelacion=p.get("politica_cancelacion", ""),
                lugares_destacados=p.get("lugares_destacados", ""),
                documentos_requeridos=p.get("documentos_requeridos", ""),
                temperatura=p.get("temperatura", ""),
                precio_aplica_desde=p.get("precio_aplica_desde"),
                precio_aplica_hasta=p.get("precio_aplica_hasta"),
                incluye_vuelo=True,
                incluye_hotel=True,
                incluye_alimentacion=True,
                incluye_traslados=True,
                incluye_tours=True,
                incluye_seguro=True,
                destacado=p["destacado"],
                activo=True,
                pdf_url=PDF_DETALLE,
            )
        self.stdout.write(f"Paquetes Turísticos creados: {PaqueteTuristico.objects.count()}")
