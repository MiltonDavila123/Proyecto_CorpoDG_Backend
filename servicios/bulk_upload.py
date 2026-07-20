"""Carga masiva de Paquetes, Vuelos y Destinos desde archivos CSV.

Las columnas de los CSV usan identificadores legibles (códigos y nombres),
no IDs de base de datos, para que cualquier persona pueda llenar la plantilla:

  - region        -> clave de Region (caribe, sudamerica, ..., ecuador)
  - pais_iso      -> codigo_iso del país (EC, US, ES, MX, CO, PE, DO, ...)
  - ciudad_codigo -> codigo_ciudad de la ciudad (UIO, GYE, ...) dentro del país
  - aerolinea     -> código IATA (LA, AV) o nombre de la aerolínea
  - *_iata        -> código IATA del aeropuerto (UIO, GYE, MIA, ...)
  - tipo_paquete / temporada / tipo_viaje -> nombre exacto

Cada fila se procesa de forma aislada: si una falla, las demás igual se cargan
y se reporta el error de esa fila. Se hace "update_or_create" por una clave
natural, de modo que volver a subir el mismo archivo actualiza en vez de
duplicar.
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.core.exceptions import ValidationError

from .models import (
    Region, PaisRegion, Ciudad, Aerolinea, Aeropuerto,
    Vuelo, Destino, PaqueteTuristico, TipoPaquete, Temporada, TipoViaje,
)

# ---------------------------------------------------------------------------
# Definición de columnas de cada plantilla: (columna, ejemplo)
# El orden define el orden de las columnas en el CSV de plantilla.
# ---------------------------------------------------------------------------

COLUMNAS_DESTINOS = [
    ("nombre", "Islas Galápagos"),
    ("pais_iso", "EC"),
    ("ciudad_codigo", "GPS"),
    ("descripcion", "Fauna única y paisajes volcánicos de las Islas Encantadas"),
    ("imagen_url", "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=600"),
    ("precio_desde", "1599"),
    ("destacado", "si"),
    ("activo", "si"),
    ("pdf_url", ""),
    ("mensaje_reserva", "Me interesa el destino Islas Galápagos"),
]

COLUMNAS_VUELOS = [
    ("aerolinea", "LA"),
    ("origen_iata", "UIO"),
    ("destino_iata", "MIA"),
    ("duracion", "4h 20m"),
    ("precio", "430"),
    ("moneda", "USD"),
    ("imagen_url", ""),
    ("destacado", "no"),
    ("disponible", "si"),
    ("mensaje_reserva", "Me interesa este vuelo"),
]

COLUMNAS_PAQUETES = [
    ("titulo", "Galápagos Express"),
    ("subtitulo", "4 días / 3 noches"),
    ("region", "sudamerica"),
    ("pais_iso", "EC"),
    ("ciudad_codigo", "GPS"),
    ("precio", "1299"),
    ("moneda", "USD"),
    ("tipo_paquete", "Aventura"),
    ("temporada", "Alta"),
    ("tipo_viaje", "Ida y Vuelta"),
    ("aerolinea", "LA"),
    ("duracion_dias", "4"),
    ("duracion_noches", "3"),
    ("salidas", "Quito y Guayaquil"),
    ("fecha_salidas_texto", "Enero a Diciembre 2026"),
    ("imagen_url", "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=600"),
    ("descripcion_corta", "Descubre la magia de las Islas Galápagos en 4 días."),
    ("titulo_detalle", "GALÁPAGOS EXPRESS — 4 DÍAS / 3 NOCHES"),
    ("descripcion_extensa", "Aventura inolvidable a las Islas Galápagos.\\nDía 1: Llegada.\\nDía 2: Tour."),
    ("precio_aplica_desde", "2026-01-01"),
    ("precio_aplica_hasta", "2026-12-31"),
    ("ubicacion_mapa_url", ""),
    ("idioma", "Español"),
    ("moneda_local", "Dólar Americano"),
    ("temperatura", "24°C - 30°C"),
    ("lugares_destacados", "Estación Charles Darwin,Bahía Tortuga,La Lobería"),
    ("documentos_requeridos", "Pasaporte vigente"),
    ("programa_incluye", "Vuelo ida y vuelta\\nAlojamiento 3 noches\\nDesayunos"),
    ("no_incluye", "Comidas no especificadas\\nPropinas\\nGastos personales"),
    ("como_reservar", "Contáctanos por el formulario web o WhatsApp."),
    ("importante", "Precios sujetos a disponibilidad."),
    ("horarios_vuelo", "Salida 08:00 - Regreso 18:00"),
    ("politicas_equipaje", "1 maleta 23kg + 1 carry-on 10kg"),
    ("requisitos_viaje", "Pasaporte vigente (mínimo 6 meses)"),
    ("formas_pago", "Transferencia\\nTarjetas de crédito\\nStripe"),
    ("politica_cancelacion", "Hasta 30 días: 90% de reembolso"),
    ("incluye_vuelo", "si"),
    ("incluye_hotel", "si"),
    ("incluye_alimentacion", "no"),
    ("incluye_traslados", "si"),
    ("incluye_tours", "si"),
    ("incluye_seguro", "no"),
    ("pdf_url", ""),
    ("mensaje_reserva", "Me interesa el Paquete Galápagos Express"),
    ("destacado", "si"),
    ("activo", "si"),
]

PLANTILLAS = {
    "destinos": COLUMNAS_DESTINOS,
    "vuelos": COLUMNAS_VUELOS,
    "paquetes": COLUMNAS_PAQUETES,
}


# ---------------------------------------------------------------------------
# Generación del CSV de plantilla (encabezado + una fila de ejemplo)
# ---------------------------------------------------------------------------

def generar_plantilla_csv(tipo):
    """Devuelve el contenido (str) del CSV de plantilla para el tipo dado."""
    columnas = PLANTILLAS[tipo]
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([c for c, _ in columnas])
    writer.writerow([ej for _, ej in columnas])
    return "\ufeff" + buffer.getvalue()  # BOM para Excel


# ---------------------------------------------------------------------------
# Conversores de valores
# ---------------------------------------------------------------------------

_VERDADEROS = {"1", "true", "si", "sí", "yes", "x", "verdadero", "y", "t"}
_FALSOS = {"0", "false", "no", "n", "f", "falso", ""}


def _bool(valor, default=False):
    if valor is None:
        return default
    v = str(valor).strip().lower()
    if v in _VERDADEROS:
        return True
    if v in _FALSOS:
        return default if v == "" else False
    return default


def _texto(valor):
    """Limpia y convierte los '\\n' literales del CSV en saltos de línea reales."""
    if valor is None:
        return ""
    return str(valor).replace("\\n", "\n").strip()


def _decimal(valor, campo):
    v = str(valor or "").strip().replace(",", ".")
    if not v:
        raise ValueError(f"falta el valor numérico '{campo}'")
    try:
        return Decimal(v)
    except InvalidOperation:
        raise ValueError(f"'{campo}' no es un número válido: '{valor}'")


def _entero(valor, campo, default=None):
    v = str(valor or "").strip()
    if not v:
        if default is not None:
            return default
        raise ValueError(f"falta el valor entero '{campo}'")
    try:
        return int(float(v))
    except ValueError:
        raise ValueError(f"'{campo}' no es un entero válido: '{valor}'")


def _fecha(valor, campo):
    v = str(valor or "").strip()
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"'{campo}' debe tener formato AAAA-MM-DD: '{valor}'")


# ---------------------------------------------------------------------------
# Resolución de llaves foráneas por identificadores legibles
# ---------------------------------------------------------------------------

def _resolver_region(clave):
    v = str(clave or "").strip().lower()
    if not v:
        raise ValueError("falta 'region'")
    region = Region.objects.filter(nombre=v).first()
    if not region:
        # permitir también el nombre visible (ej: "Sudamérica")
        for r in Region.objects.all():
            if r.get_nombre_display().lower() == v:
                region = r
                break
    if not region:
        validos = ", ".join(Region.objects.values_list("nombre", flat=True))
        raise ValueError(f"región '{clave}' no encontrada (válidas: {validos})")
    return region


def _resolver_pais(iso, requerido=True):
    v = str(iso or "").strip().upper()
    if not v:
        if requerido:
            raise ValueError("falta 'pais_iso'")
        return None
    pais = PaisRegion.objects.filter(codigo_iso__iexact=v).first()
    if not pais:
        raise ValueError(f"país con código ISO '{iso}' no encontrado")
    return pais


def _resolver_ciudad(pais, codigo):
    v = str(codigo or "").strip().upper()
    if not v:
        return None
    qs = Ciudad.objects.filter(codigo_ciudad__iexact=v)
    if pais:
        qs = qs.filter(pais=pais)
    ciudad = qs.first()
    if not ciudad:
        ambito = f" en {pais.nombre}" if pais else ""
        raise ValueError(f"ciudad con código '{codigo}' no encontrada{ambito}")
    return ciudad


def _resolver_aerolinea(valor, requerido=False):
    v = str(valor or "").strip()
    if not v:
        if requerido:
            raise ValueError("falta 'aerolinea'")
        return None
    aero = Aerolinea.objects.filter(codigo_iata__iexact=v).first()
    if not aero:
        aero = Aerolinea.objects.filter(nombre__icontains=v).first()
    if not aero:
        raise ValueError(f"aerolínea '{valor}' no encontrada (IATA o nombre)")
    return aero


def _resolver_aeropuerto(iata, campo):
    v = str(iata or "").strip().upper()
    if not v:
        raise ValueError(f"falta '{campo}'")
    aeropuerto = Aeropuerto.objects.filter(codigo_iata__iexact=v).first()
    if not aeropuerto:
        raise ValueError(f"aeropuerto con código IATA '{iata}' no encontrado ({campo})")
    return aeropuerto


def _resolver_catalogo(modelo, nombre, etiqueta):
    v = str(nombre or "").strip()
    if not v:
        return None
    obj = modelo.objects.filter(nombre__iexact=v).first()
    if not obj:
        raise ValueError(f"{etiqueta} '{nombre}' no encontrado")
    return obj


# ---------------------------------------------------------------------------
# Procesadores por tipo (devuelven "creado" | "actualizado")
# ---------------------------------------------------------------------------

def _procesar_destino(fila):
    nombre = (fila.get("nombre") or "").strip()
    if not nombre:
        raise ValueError("falta 'nombre'")
    pais = _resolver_pais(fila.get("pais_iso"), requerido=False)
    ciudad = _resolver_ciudad(pais, fila.get("ciudad_codigo"))
    if not pais and ciudad:
        pais = ciudad.pais
    if not pais and not ciudad:
        raise ValueError("debe indicar 'pais_iso' o 'ciudad_codigo'")

    obj = Destino.objects.filter(nombre__iexact=nombre, pais=pais).first()
    accion = "actualizado" if obj else "creado"
    obj = obj or Destino()
    obj.nombre = nombre
    obj.pais = pais
    obj.ciudad = ciudad
    obj.descripcion = _texto(fila.get("descripcion"))
    obj.imagen_url = (fila.get("imagen_url") or "").strip()
    obj.precio_desde = _decimal(fila.get("precio_desde"), "precio_desde")
    obj.destacado = _bool(fila.get("destacado"), default=False)
    obj.activo = _bool(fila.get("activo"), default=True)
    obj.pdf_url = (fila.get("pdf_url") or "").strip() or None
    obj.mensaje_reserva = _texto(fila.get("mensaje_reserva"))
    obj.full_clean()
    obj.save()
    return accion


def _procesar_vuelo(fila):
    aerolinea = _resolver_aerolinea(fila.get("aerolinea"), requerido=True)
    origen = _resolver_aeropuerto(fila.get("origen_iata"), "origen_iata")
    destino = _resolver_aeropuerto(fila.get("destino_iata"), "destino_iata")

    obj = Vuelo.objects.filter(
        aerolinea=aerolinea, origen=origen, destino=destino
    ).first()
    accion = "actualizado" if obj else "creado"
    obj = obj or Vuelo()
    obj.aerolinea = aerolinea
    obj.origen = origen
    obj.destino = destino
    obj.duracion = (fila.get("duracion") or "").strip()
    obj.precio = _decimal(fila.get("precio"), "precio")
    obj.moneda = (fila.get("moneda") or "USD").strip() or "USD"
    obj.imagen_url = (fila.get("imagen_url") or "").strip() or None
    obj.destacado = _bool(fila.get("destacado"), default=False)
    obj.disponible = _bool(fila.get("disponible"), default=True)
    obj.mensaje_reserva = _texto(fila.get("mensaje_reserva"))
    obj.full_clean()
    obj.save()
    return accion


def _procesar_paquete(fila):
    titulo = (fila.get("titulo") or "").strip()
    if not titulo:
        raise ValueError("falta 'titulo'")
    region = _resolver_region(fila.get("region"))
    pais = _resolver_pais(fila.get("pais_iso"), requerido=True)
    ciudad = _resolver_ciudad(pais, fila.get("ciudad_codigo"))

    obj = PaqueteTuristico.objects.filter(titulo__iexact=titulo).first()
    accion = "actualizado" if obj else "creado"
    obj = obj or PaqueteTuristico()

    obj.titulo = titulo
    obj.subtitulo = (fila.get("subtitulo") or "").strip()
    obj.region = region
    obj.pais_destino = pais
    obj.ciudad_destino = ciudad
    obj.precio = _decimal(fila.get("precio"), "precio")
    obj.moneda = (fila.get("moneda") or "USD").strip() or "USD"
    obj.tipo_paquete = _resolver_catalogo(TipoPaquete, fila.get("tipo_paquete"), "tipo de paquete")
    obj.temporada = _resolver_catalogo(Temporada, fila.get("temporada"), "temporada")
    obj.tipo_viaje = _resolver_catalogo(TipoViaje, fila.get("tipo_viaje"), "tipo de viaje")
    obj.aerolinea = _resolver_aerolinea(fila.get("aerolinea"), requerido=False)
    obj.duracion_dias = _entero(fila.get("duracion_dias"), "duracion_dias", default=1)
    obj.duracion_noches = _entero(fila.get("duracion_noches"), "duracion_noches")
    obj.salidas = (fila.get("salidas") or "").strip()
    obj.fecha_salidas_texto = (fila.get("fecha_salidas_texto") or "").strip()
    obj.imagen_url = (fila.get("imagen_url") or "").strip()
    obj.descripcion_corta = _texto(fila.get("descripcion_corta"))
    obj.titulo_detalle = (fila.get("titulo_detalle") or "").strip()
    obj.descripcion_extensa = _texto(fila.get("descripcion_extensa"))
    obj.precio_aplica_desde = _fecha(fila.get("precio_aplica_desde"), "precio_aplica_desde")
    obj.precio_aplica_hasta = _fecha(fila.get("precio_aplica_hasta"), "precio_aplica_hasta")
    obj.ubicacion_mapa_url = (fila.get("ubicacion_mapa_url") or "").strip() or None
    obj.idioma = (fila.get("idioma") or "").strip()
    obj.moneda_local = (fila.get("moneda_local") or "").strip()
    obj.temperatura = (fila.get("temperatura") or "").strip()
    obj.lugares_destacados = _texto(fila.get("lugares_destacados"))
    obj.documentos_requeridos = _texto(fila.get("documentos_requeridos"))
    obj.programa_incluye = _texto(fila.get("programa_incluye"))
    obj.no_incluye = _texto(fila.get("no_incluye"))
    obj.como_reservar = _texto(fila.get("como_reservar"))
    obj.importante = _texto(fila.get("importante"))
    obj.horarios_vuelo = _texto(fila.get("horarios_vuelo"))
    obj.politicas_equipaje = _texto(fila.get("politicas_equipaje"))
    obj.requisitos_viaje = _texto(fila.get("requisitos_viaje"))
    obj.formas_pago = _texto(fila.get("formas_pago"))
    obj.politica_cancelacion = _texto(fila.get("politica_cancelacion"))
    obj.incluye_vuelo = _bool(fila.get("incluye_vuelo"), default=True)
    obj.incluye_hotel = _bool(fila.get("incluye_hotel"), default=True)
    obj.incluye_alimentacion = _bool(fila.get("incluye_alimentacion"), default=False)
    obj.incluye_traslados = _bool(fila.get("incluye_traslados"), default=False)
    obj.incluye_tours = _bool(fila.get("incluye_tours"), default=False)
    obj.incluye_seguro = _bool(fila.get("incluye_seguro"), default=False)
    obj.pdf_url = (fila.get("pdf_url") or "").strip() or None
    obj.mensaje_reserva = _texto(fila.get("mensaje_reserva"))
    obj.destacado = _bool(fila.get("destacado"), default=False)
    obj.activo = _bool(fila.get("activo"), default=True)
    obj.full_clean()
    obj.save()
    return accion


_PROCESADORES = {
    "destinos": _procesar_destino,
    "vuelos": _procesar_vuelo,
    "paquetes": _procesar_paquete,
}


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def procesar_csv(tipo, archivo_bytes):
    """Procesa el CSV subido y devuelve un resumen del resultado.

    Args:
        tipo: 'destinos' | 'vuelos' | 'paquetes'
        archivo_bytes: contenido del archivo subido (bytes)

    Returns:
        dict con: creados, actualizados, errores (lista de {fila, mensaje}),
        total, columnas_esperadas, columnas_recibidas.
    """
    if tipo not in _PROCESADORES:
        return {"error": f"Tipo desconocido: {tipo}"}

    try:
        texto = archivo_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = archivo_bytes.decode("latin-1")

    # Detectar el separador (; de Excel-ES o , estándar)
    primera_linea = texto.splitlines()[0] if texto.strip() else ""
    delimitador = ";" if primera_linea.count(";") >= primera_linea.count(",") else ","

    reader = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
    columnas_esperadas = [c for c, _ in PLANTILLAS[tipo]]
    columnas_recibidas = [(c or "").strip() for c in (reader.fieldnames or [])]

    procesador = _PROCESADORES[tipo]
    creados = actualizados = 0
    errores = []
    total = 0

    from django.db import transaction

    for i, fila in enumerate(reader, start=2):  # fila 1 = encabezado
        # normalizar claves (quitar espacios/BOM)
        fila = {(k or "").strip(): (v if v is not None else "") for k, v in fila.items()}
        if not any((v or "").strip() for v in fila.values()):
            continue  # fila vacía
        total += 1
        try:
            with transaction.atomic():
                accion = procesador(fila)
            if accion == "creado":
                creados += 1
            else:
                actualizados += 1
        except ValidationError as e:
            msgs = "; ".join(
                f"{campo}: {', '.join(map(str, errs))}"
                for campo, errs in e.message_dict.items()
            ) if hasattr(e, "message_dict") else "; ".join(map(str, e.messages))
            errores.append({"fila": i, "mensaje": msgs})
        except ValueError as e:
            errores.append({"fila": i, "mensaje": str(e)})
        except Exception as e:  # noqa: BLE001
            errores.append({"fila": i, "mensaje": f"error inesperado: {e}"})

    return {
        "creados": creados,
        "actualizados": actualizados,
        "errores": errores,
        "total": total,
        "columnas_esperadas": columnas_esperadas,
        "columnas_recibidas": columnas_recibidas,
    }
