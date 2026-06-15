"""Get Seats (mapa de asientos) via Sabre.

POST https://api.cert.platform.sabre.com/v3/offers/getseats/byReservationPayload

Recibe un itinerario tal como lo devuelve la busqueda enriquecida +
pasajeros, arma el payload de Sabre y devuelve un mapa de asientos
normalizado para el frontend.

MODO SANDBOX:
  Si la setting SEATMAP_SANDBOX es True (o env SEATMAP_SANDBOX=1), no se
  consulta Sabre y se devuelve una respuesta simulada con la MISMA
  estructura del API real (seatMaps, cabinCompartments, seatRows,
  priceDefinitions, offerItems, serviceDefinitions). Permite que el
  frontend ya integre la pantalla mientras Sabre habilita el PCC para
  el endpoint Get Seats.
"""

import datetime as _dt
import os
import random
import uuid

import requests

try:
    from django.conf import settings as _django_settings
except ImportError:  # pragma: no cover
    _django_settings = None

from .LlamadosAPIS.Llamado_Api_TOKEN import SabreAuthError, obtener_token_sabre

SABRE_SEATMAP_URL = (
    "https://api.cert.platform.sabre.com/v3/offers/getseats/byReservationPayload"
)


def _sandbox_activo():
    if _django_settings is not None:
        try:
            if getattr(_django_settings, "SEATMAP_SANDBOX", None) is not None:
                return bool(_django_settings.SEATMAP_SANDBOX)
        except AttributeError:
            pass
    env = os.getenv("SEATMAP_SANDBOX")
    if env is None:
        return True  # por defecto sandbox ON hasta que Sabre habilite PCC
    return env.strip().lower() in ("1", "true", "yes", "on")


def _gen_id(prefijo):
    return f"{prefijo}-{uuid.uuid4()}"


def _llamar_seatmap(payload, force_refresh=False):
    token = obtener_token_sabre(force_refresh=force_refresh)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Conversation-ID": "corpodg-seatmap",
        "X-Sabre-PseudoCityCode": "DQ2J",
    }
    return requests.post(SABRE_SEATMAP_URL, headers=headers, json=payload, timeout=30)


def _normalizar_segmento(seg):
    """Soporta formato enriquecido y formato plano (igual que revalidate)."""
    salida = seg.get("salida") or {}
    llegada = seg.get("llegada") or {}
    aerolinea = seg.get("aerolinea") or {}

    marketing = seg.get("aerolinea_marketing") or aerolinea.get("codigo")
    operadora = (
        seg.get("aerolinea_operadora")
        or aerolinea.get("operada_por")
        or marketing
    )
    numero_vuelo = seg.get("numero_vuelo")
    if numero_vuelo is None and seg.get("vuelo") and marketing:
        resto = seg["vuelo"].replace(marketing, "", 1)
        numero_vuelo = int(resto) if resto.isdigit() else None
    numero_op = seg.get("numero_vuelo_operador") or numero_vuelo

    fhs = seg.get("fecha_hora_salida") or ""
    fhl = seg.get("fecha_hora_llegada") or ""
    fecha_salida, _, hora_salida = fhs.partition("T")
    fecha_llegada, _, hora_llegada = fhl.partition("T")

    return {
        "origen": seg.get("origen") or salida.get("aeropuerto"),
        "destino": seg.get("destino") or llegada.get("aeropuerto"),
        "marketing": marketing,
        "operadora": operadora,
        "numero_vuelo": numero_vuelo,
        "numero_vuelo_operador": numero_op,
        "clase_servicio": seg.get("clase_servicio"),
        "cabina": seg.get("cabina") or "Y",
        "fare_basis": seg.get("fare_basis"),
        "fecha_salida": seg.get("fecha_salida") or fecha_salida,
        "fecha_llegada": seg.get("fecha_llegada") or fecha_llegada,
        "hora_salida": (hora_salida or "00:00")[:5],
        "hora_llegada": (hora_llegada or "00:00")[:5],
    }


def _aplanar_segmentos(tramos):
    out = []
    for tramo in tramos:
        for seg in tramo.get("segmentos") or []:
            out.append(_normalizar_segmento(seg))
    return out


def _construir_payload(opcion, pasajeros, moneda="USD"):
    tramos = opcion.get("tramos") or []
    if not tramos:
        raise ValueError("opcion sin tramos")

    segmentos = _aplanar_segmentos(tramos)
    if not segmentos:
        raise ValueError("no hay segmentos")

    fare_info = opcion.get("fare_info") or []
    if not fare_info:
        raise ValueError("opcion sin fare_info; reejecuta la busqueda con la version nueva")

    # IDs
    seg_ids = [_gen_id("SEG") for _ in segmentos]
    pax_ids = [_gen_id("PAX") for _ in pasajeros]
    fc_ids = [_gen_id("FC") for _ in fare_info]

    # Mapear cada segmento a su fareComponent por rango begin->end (igual que searchFlights)
    seg_to_fc = []
    fc_idx = 0
    for s in segmentos:
        if fc_idx < len(fare_info):
            seg_to_fc.append(fc_idx)
            if s["destino"] == fare_info[fc_idx].get("end"):
                fc_idx += 1
        else:
            seg_to_fc.append(len(fare_info) - 1)

    # Construir segmentos de Sabre
    sabre_segments = []
    for i, s in enumerate(segmentos):
        fci = fare_info[seg_to_fc[i]]
        sabre_segments.append({
            "id": seg_ids[i],
            "bookingAirlineCode": s["marketing"],
            "bookingFlightNumber": int(s["numero_vuelo"]),
            "departureAirportCode": s["origen"],
            "arrivalAirportCode": s["destino"],
            "departureDate": s["fecha_salida"],
            "departureTime": s["hora_salida"],
            "arrivalDate": s["fecha_llegada"],
            "arrivalTime": s["hora_llegada"],
            "bookingClassCode": s["clase_servicio"],
            "operatingAirlineCode": s["operadora"] or s["marketing"],
            "operatingFlightNumber": int(s["numero_vuelo_operador"] or s["numero_vuelo"]),
            "operatingBookingClassCode": s["clase_servicio"],
            "cabinCode": s["cabina"] or fci.get("cabin") or "Y",
            "hasRecordCreateTag": False,
        })

    # Pasajeros
    sabre_passengers = []
    for i, p in enumerate(pasajeros):
        fare_assoc = [
            {"segmentRef": seg_ids[idx], "fareComponentRef": fc_ids[seg_to_fc[idx]]}
            for idx in range(len(segmentos))
        ]
        sabre_passengers.append({
            "id": pax_ids[i],
            "passengerType": p.get("passengerType") or "ADT",
            "givenName": (p.get("givenName") or "TEST").upper(),
            "surname": (p.get("surname") or "TEST").upper(),
            "fareSegmentAssociation": fare_assoc,
        })

    # fareComponents
    sabre_fcs = []
    for i, fci in enumerate(fare_info):
        sabre_fcs.append({
            "fareComponentId": fc_ids[i],
            "governingCarrier": fci.get("governing_carrier") or segmentos[0]["marketing"],
            "totalPrice": str(fci.get("fare_amount") or opcion.get("precio_base") or "0"),
            "totalPriceCurrencyCode": fci.get("fare_currency") or moneda,
            "fareBasis": fci.get("fare_basis") or "",
            **({"brandCode": fci["brand_code"]} if fci.get("brand_code") else {}),
        })

    payload = {
        "posDetails": {
            "pcc": "DQ2J",
            "pseudoCityCode": "DQ2J",
        },
        "pointOfSale": {"pseudoCityCode": "DQ2J"},
        "pos": {"pcc": "DQ2J", "pseudoCityCode": "DQ2J"},
        "agency": {"pseudoCityCode": "DQ2J"},
        "agencyOptions": {"pseudoCityCode": "DQ2J"},
        "segments": sabre_segments,
        "passengers": sabre_passengers,
        "fareComponents": sabre_fcs,
        "currencyCode": moneda,
        "isCheckinMode": False,
    }
    return payload, seg_ids, pax_ids


def _normalizar_respuesta(raw, seg_ids):
    """Aplana el JSON de Sabre para que sea facil de pintar en el frontend."""
    resp = raw.get("response") or {}
    seat_maps = resp.get("seatMaps") or []
    price_defs = {p["id"]: p for p in (resp.get("priceDefinitions") or [])}
    service_defs = {s["id"]: s for s in (resp.get("serviceDefinitions") or [])}
    offer_items = {o["id"]: o for o in (resp.get("offerItems") or [])}
    segments_meta = {s["id"]: s for s in (resp.get("segments") or [])}

    # Mapa seg_id sabre -> indice del segmento original (orden enviado)
    seg_index = {sid: idx + 1 for idx, sid in enumerate(seg_ids)}

    mapas = []
    for sm in seat_maps:
        seg_id = sm.get("segmentRef")
        meta = segments_meta.get(seg_id, {})
        cabinas = []
        for comp in sm.get("cabinCompartments") or []:
            layout = comp.get("cabinLayout") or {}
            columnas = [
                {
                    "letra": c.get("id"),
                    "posiciones": c.get("position") or [],
                }
                for c in (layout.get("columns") or [])
            ]
            filas = []
            for fila in comp.get("seatRows") or []:
                asientos = []
                for a in fila.get("seats") or []:
                    precio = None
                    nombre_servicio = None
                    for oid in a.get("offerItemRefIds") or []:
                        item = offer_items.get(oid) or {}
                        pdef = price_defs.get(item.get("priceDefinitionRef")) or {}
                        total = (pdef.get("totalPrice") or {})
                        if total.get("amount"):
                            precio = {
                                "monto": float(total["amount"]),
                                "moneda": pdef.get("currencyCode") or "USD",
                                "purchase_by": item.get("purchaseByDateTime"),
                                "offer_item_id": oid,
                            }
                        sdef = service_defs.get(item.get("serviceDefinitionRef")) or {}
                        nombre_servicio = sdef.get("commercialName")
                        if precio:
                            break
                    asientos.append({
                        "id": f"{fila.get('row')}{a.get('column')}",
                        "columna": a.get("column"),
                        "fila": fila.get("row"),
                        "disponible": a.get("occupationStatusCode") == "F"
                                      and a.get("isOperative") is not False,
                        "estado": a.get("occupationStatusCode"),
                        "caracteristicas": [
                            c.get("description") or c.get("code")
                            for c in (a.get("characteristics") or [])
                        ],
                        "servicio": nombre_servicio,
                        "precio": precio,
                    })
                filas.append({
                    "numero": fila.get("row"),
                    "caracteristicas": [
                        c.get("description") or c.get("code")
                        for c in (fila.get("characteristics") or [])
                    ],
                    "asientos": asientos,
                })
            cabinas.append({
                "codigo": comp.get("cabinCode"),
                "nombre": comp.get("cabinName"),
                "fila_inicial": comp.get("firstRow"),
                "fila_final": comp.get("lastRow"),
                "columnas": columnas,
                "filas": filas,
            })

        mapas.append({
            "segmento_id_sabre": seg_id,
            "segmento_indice": seg_index.get(seg_id),
            "vuelo": f"{meta.get('bookingAirlineCode','')}{meta.get('bookingFlightNumber','')}",
            "origen": meta.get("departureAirportCode"),
            "destino": meta.get("arrivalAirportCode"),
            "cabinas": cabinas,
        })

    return {
        "offer_id": resp.get("offerId"),
        "expira": resp.get("offerExpirationDateTime"),
        "mapas": mapas,
    }


def obtener_mapa_asientos(datos):
    opcion = datos.get("opcion") or {}
    pasajeros = datos.get("pasajeros") or [{"passengerType": "ADT",
                                            "givenName": "TEST",
                                            "surname": "TEST"}]
    moneda = datos.get("moneda") or opcion.get("moneda") or "USD"

    if not opcion.get("tramos"):
        return {"error": "Debe enviar 'opcion' con sus 'tramos'", "code": 400}

    try:
        payload, seg_ids, _ = _construir_payload(opcion, pasajeros, moneda)
    except (KeyError, TypeError, ValueError) as e:
        return {"error": f"Datos incompletos: {e}", "code": 400}

    if _sandbox_activo() or datos.get("sandbox") is True:
        raw = _simular_respuesta_sabre(payload, seg_ids, moneda)
        normalizado = _normalizar_respuesta(raw, seg_ids)
        normalizado["sandbox"] = True
        normalizado["warnings"] = []
        return normalizado

    try:
        response = _llamar_seatmap(payload)
        if response.status_code == 401:
            response = _llamar_seatmap(payload, force_refresh=True)

        try:
            raw = response.json()
        except ValueError:
            return {"error": "Respuesta de Sabre no es JSON",
                    "code": response.status_code,
                    "raw": response.text[:500]}

        if response.status_code != 200:
            return {"error": "Sabre rechazo la peticion",
                    "code": response.status_code,
                    "detalle": raw}

        errores = raw.get("errors") or []
        # Solo errores criticos (no warnings)
        criticos = [e for e in errores if (e.get("category") or "").upper() in
                    ("BAD_REQUEST", "SERVER_ERROR", "UNAUTHORIZED",
                     "VALIDATION", "NOT_FOUND")]
        if criticos and not (raw.get("response") or {}).get("seatMaps"):
            return {"error": "Sabre no pudo generar el mapa",
                    "code": 422,
                    "detalle": criticos}

        normalizado = _normalizar_respuesta(raw, seg_ids)
        if not normalizado["mapas"]:
            return {"error": "La aerolinea no expone mapa de asientos para este vuelo",
                    "code": 404,
                    "warnings": raw.get("warnings") or []}

        normalizado["warnings"] = raw.get("warnings") or []
        return normalizado

    except (requests.RequestException, SabreAuthError) as e:
        return {"error": str(e), "code": 500}


# ---------------------------------------------------------------------------
# SANDBOX: respuesta simulada con la misma estructura que Sabre Get Seats v3
# ---------------------------------------------------------------------------

# Catalogo basico de caracteristicas de asiento usado por el simulador.
_CHAR_WINDOW = {"code": "W", "description": "Window"}
_CHAR_AISLE = {"code": "A", "description": "Aisle"}
_CHAR_MIDDLE = {"code": "M", "description": "Middle"}
_CHAR_LEGROOM = {"code": "L", "description": "Extra legroom"}
_CHAR_EXIT = {"code": "E", "description": "Exit row"}
_CHAR_BULKHEAD = {"code": "K", "description": "Bulkhead"}
_CHAR_RECLINE = {"code": "1", "description": "Reclining seat"}
_CHAR_QUIET = {"code": "Q", "description": "Quiet zone"}
_CHAR_NEAR_LAV = {"code": "LAV", "description": "Near lavatory"}

# Cabinas tipicas por codigo de cabina.
_CABIN_LAYOUTS = {
    "F": {  # First
        "cabinCode": "F",
        "cabinName": "First Class",
        "columns": [
            {"id": "A", "position": ["WINDOW"]},
            {"id": "D", "position": ["AISLE"]},
            {"id": "G", "position": ["AISLE"]},
            {"id": "K", "position": ["WINDOW"]},
        ],
        "first_row": 1,
        "last_row": 3,
        "base_price": 0,
    },
    "J": {  # Business
        "cabinCode": "C",
        "cabinName": "Business Class",
        "columns": [
            {"id": "A", "position": ["WINDOW"]},
            {"id": "C", "position": ["AISLE"]},
            {"id": "D", "position": ["AISLE"]},
            {"id": "G", "position": ["AISLE"]},
            {"id": "H", "position": ["AISLE"]},
            {"id": "K", "position": ["WINDOW"]},
        ],
        "first_row": 4,
        "last_row": 9,
        "base_price": 0,
    },
    "C": {
        "cabinCode": "C",
        "cabinName": "Business Class",
        "columns": [
            {"id": "A", "position": ["WINDOW"]},
            {"id": "C", "position": ["AISLE"]},
            {"id": "D", "position": ["AISLE"]},
            {"id": "G", "position": ["AISLE"]},
            {"id": "H", "position": ["AISLE"]},
            {"id": "K", "position": ["WINDOW"]},
        ],
        "first_row": 4,
        "last_row": 9,
        "base_price": 0,
    },
    "W": {  # Premium Economy
        "cabinCode": "W",
        "cabinName": "Premium Economy",
        "columns": [
            {"id": "A", "position": ["WINDOW"]},
            {"id": "B", "position": ["CENTER"]},
            {"id": "C", "position": ["AISLE"]},
            {"id": "D", "position": ["AISLE"]},
            {"id": "E", "position": ["CENTER"]},
            {"id": "F", "position": ["WINDOW"]},
        ],
        "first_row": 10,
        "last_row": 14,
        "base_price": 45.0,
    },
    "Y": {  # Economy
        "cabinCode": "Y",
        "cabinName": "Economy Class",
        "columns": [
            {"id": "A", "position": ["WINDOW"]},
            {"id": "B", "position": ["CENTER"]},
            {"id": "C", "position": ["AISLE"]},
            {"id": "D", "position": ["AISLE"]},
            {"id": "E", "position": ["CENTER"]},
            {"id": "F", "position": ["WINDOW"]},
        ],
        "first_row": 15,
        "last_row": 34,
        "base_price": 0,
    },
}


def _seed_para_segmento(seg):
    """(No usado; mantenido por compatibilidad). Antes daba semilla estable."""
    return 0


def _columna_es_ventana(col_id, columnas):
    return col_id in (columnas[0]["id"], columnas[-1]["id"])


def _columna_es_pasillo(col_id, columnas):
    # pasillo = letra inmediatamente antes o despues del salto central
    n = len(columnas)
    mitad = n // 2
    return col_id in (columnas[mitad - 1]["id"], columnas[mitad]["id"])


def _caracteristicas_asiento(col_id, fila, columnas, exit_rows, bulkhead_row):
    chars = []
    if _columna_es_ventana(col_id, columnas):
        chars.append(_CHAR_WINDOW)
    elif _columna_es_pasillo(col_id, columnas):
        chars.append(_CHAR_AISLE)
    else:
        chars.append(_CHAR_MIDDLE)
    if fila in exit_rows:
        chars.append(_CHAR_EXIT)
        chars.append(_CHAR_LEGROOM)
    if fila == bulkhead_row:
        chars.append(_CHAR_BULKHEAD)
        chars.append(_CHAR_LEGROOM)
    chars.append(_CHAR_RECLINE)
    return chars


def _calc_precio(base, fila, col_id, columnas, exit_rows, bulkhead_row, currency):
    monto = base
    if fila in exit_rows or fila == bulkhead_row:
        monto += 25.0
    if _columna_es_ventana(col_id, columnas):
        monto += 8.0
    elif _columna_es_pasillo(col_id, columnas):
        monto += 6.0
    if monto <= 0:
        return None
    return round(monto, 2)


def _simular_respuesta_sabre(payload, seg_ids, currency):
    rnd_global = random.Random()
    offer_id = f"SIM-{rnd_global.randint(10**11, 10**12 - 1)}"
    expira = (_dt.datetime.utcnow() + _dt.timedelta(hours=2)) \
        .strftime("%Y-%m-%dT%H:%M:%SZ")

    service_definitions = [{
        "id": "SVC-SEAT-STD",
        "commercialName": "Standard seat",
        "code": "SEAT",
    }, {
        "id": "SVC-SEAT-PREF",
        "commercialName": "Preferred seat",
        "code": "PREF",
    }, {
        "id": "SVC-SEAT-LEG",
        "commercialName": "Extra legroom seat",
        "code": "LEG",
    }]

    price_definitions = []
    offer_items = []
    seat_maps = []

    for seg in payload["segments"]:
        seg_id = seg["id"]
        rnd = random.Random()  # aleatorio en cada consulta
        cabin_code = (seg.get("cabinCode") or "Y").upper()
        layout = _CABIN_LAYOUTS.get(cabin_code) or _CABIN_LAYOUTS["Y"]

        columnas = layout["columns"]
        first_row = layout["first_row"]
        last_row = layout["last_row"]
        base_price = layout["base_price"]

        # Filas de emergencia y bulkhead aleatorias pero estables
        exit_rows = {first_row + 6, last_row - 4} if (last_row - first_row) > 8 else set()
        bulkhead_row = first_row

        seat_rows = []
        for fila in range(first_row, last_row + 1):
            seats = []
            for col in columnas:
                col_id = col["id"]
                # 22% ocupados aprox, deterministico por fila/col
                ocupado = rnd.random() < 0.22
                status = "T" if ocupado else "F"  # T=Taken, F=Free

                chars = _caracteristicas_asiento(
                    col_id, fila, columnas, exit_rows, bulkhead_row
                )

                monto = _calc_precio(
                    base_price, fila, col_id, columnas,
                    exit_rows, bulkhead_row, currency
                )

                offer_refs = []
                if monto is not None and not ocupado:
                    pdef_id = f"PDEF-{seg_id[-6:]}-{fila}{col_id}"
                    oitem_id = f"OITEM-{seg_id[-6:]}-{fila}{col_id}"
                    if fila in exit_rows or fila == bulkhead_row:
                        svc_ref = "SVC-SEAT-LEG"
                    elif monto >= 8:
                        svc_ref = "SVC-SEAT-PREF"
                    else:
                        svc_ref = "SVC-SEAT-STD"
                    price_definitions.append({
                        "id": pdef_id,
                        "totalPrice": {"amount": monto},
                        "currencyCode": currency,
                    })
                    offer_items.append({
                        "id": oitem_id,
                        "priceDefinitionRef": pdef_id,
                        "serviceDefinitionRef": svc_ref,
                        "purchaseByDateTime": expira,
                    })
                    offer_refs = [oitem_id]

                seats.append({
                    "column": col_id,
                    "occupationStatusCode": status,
                    "isOperative": True,
                    "characteristics": chars,
                    "offerItemRefIds": offer_refs,
                })

            row_chars = []
            if fila in exit_rows:
                row_chars.append(_CHAR_EXIT)
            if fila == bulkhead_row:
                row_chars.append(_CHAR_BULKHEAD)

            seat_rows.append({
                "row": fila,
                "characteristics": row_chars,
                "seats": seats,
            })

        seat_maps.append({
            "segmentRef": seg_id,
            "cabinCompartments": [{
                "cabinCode": layout["cabinCode"],
                "cabinName": layout["cabinName"],
                "firstRow": first_row,
                "lastRow": last_row,
                "cabinLayout": {"columns": columnas},
                "seatRows": seat_rows,
            }],
        })

    return {
        "response": {
            "offerId": offer_id,
            "offerExpirationDateTime": expira,
            "segments": payload["segments"],
            "passengers": payload["passengers"],
            "serviceDefinitions": service_definitions,
            "priceDefinitions": price_definitions,
            "offerItems": offer_items,
            "seatMaps": seat_maps,
        },
        "warnings": [{
            "category": "SANDBOX",
            "descriptionText": "Respuesta simulada (Sabre PCC pendiente de habilitar)",
        }],
    }
