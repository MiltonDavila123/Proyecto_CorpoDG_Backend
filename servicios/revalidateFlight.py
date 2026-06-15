"""Revalidacion de itinerarios usando Sabre Revalidate Itinerary API.

Recibe un itinerario (lista de tramos con sus segmentos) tal como lo entrega
`procesar_respuesta` en searchFlights.py y consulta al endpoint
`/v5/shop/flights/revalidate` de Sabre para confirmar si el vuelo sigue
disponible para reservar.
"""

import requests

from .LlamadosAPIS.Llamado_Api_TOKEN import SabreAuthError, obtener_token_sabre

SABRE_REVALIDATE_URL = "https://api.cert.platform.sabre.com/v5/shop/flights/revalidate"


def _llamar_revalidate(payload, force_refresh=False):
    token = obtener_token_sabre(force_refresh=force_refresh)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return requests.post(SABRE_REVALIDATE_URL, headers=headers, json=payload, timeout=30)


def _normalizar_segmento(seg):
    """Acepta tanto el formato enriquecido de procesar_respuesta como uno plano."""
    salida = seg.get("salida") or {}
    llegada = seg.get("llegada") or {}
    aerolinea = seg.get("aerolinea") or {}

    origen = seg.get("origen") or salida.get("aeropuerto")
    destino = seg.get("destino") or llegada.get("aeropuerto")
    marketing = (
        seg.get("aerolinea_marketing")
        or aerolinea.get("codigo")
    )
    operadora = (
        seg.get("aerolinea_operadora")
        or aerolinea.get("operada_por")
        or marketing
    )
    numero_vuelo = seg.get("numero_vuelo")
    if numero_vuelo is None and seg.get("vuelo") and marketing:
        # "AA833" -> 833
        resto = seg["vuelo"].replace(marketing, "", 1)
        numero_vuelo = int(resto) if resto.isdigit() else None

    return {
        "origen": origen,
        "destino": destino,
        "marketing": marketing,
        "operadora": operadora,
        "numero_vuelo": numero_vuelo,
        "clase_servicio": seg.get("clase_servicio"),
        "fecha_hora_salida": seg.get("fecha_hora_salida"),
        "fecha_hora_llegada": seg.get("fecha_hora_llegada"),
    }


def _construir_payload(tramos, pasajeros):
    origin_destinations = []
    max_stops = 0

    for tramo in tramos:
        segmentos_raw = tramo.get("segmentos") or []
        if not segmentos_raw:
            raise ValueError("Cada tramo debe incluir al menos un segmento")

        segmentos = [_normalizar_segmento(s) for s in segmentos_raw]

        for idx, s in enumerate(segmentos, start=1):
            faltantes = [
                k for k in ("origen", "destino", "marketing", "numero_vuelo",
                            "clase_servicio", "fecha_hora_salida", "fecha_hora_llegada")
                if not s.get(k)
            ]
            if faltantes:
                etiqueta = (
                    f"{s.get('marketing') or ''}{s.get('numero_vuelo') or ''}"
                    or f"#{idx}"
                )
                raise ValueError(
                    f"Segmento {idx} ({etiqueta}) incompleto, "
                    f"faltan campos: {', '.join(faltantes)}"
                )

        max_stops = max(max_stops, len(segmentos) - 1)
        primer = segmentos[0]
        ultimo = segmentos[-1]

        flights = [
            {
                "Type": "A",
                "Number": int(s["numero_vuelo"]),
                "DepartureDateTime": s["fecha_hora_salida"],
                "ArrivalDateTime": s["fecha_hora_llegada"],
                "ClassOfService": s["clase_servicio"],
                "OriginLocation": {"LocationCode": s["origen"]},
                "DestinationLocation": {"LocationCode": s["destino"]},
                "Airline": {
                    "Marketing": s["marketing"],
                    "Operating": s["operadora"] or s["marketing"],
                },
            }
            for s in segmentos
        ]

        origin_destinations.append({
            "Fixed": False,
            "DepartureDateTime": primer["fecha_hora_salida"],
            "OriginLocation": {"LocationCode": primer["origen"]},
            "DestinationLocation": {"LocationCode": ultimo["destino"]},
            "TPA_Extensions": {"Flight": flights},
        })

    air_traveler = []
    if int(pasajeros.get("adults", 0) or 0) > 0:
        air_traveler.append({"Code": "ADT", "Quantity": int(pasajeros["adults"])})
    if int(pasajeros.get("children", 0) or 0) > 0:
        air_traveler.append({"Code": "CNN", "Quantity": int(pasajeros["children"])})
    if int(pasajeros.get("infants", 0) or 0) > 0:
        air_traveler.append({"Code": "INF", "Quantity": int(pasajeros["infants"])})
    if not air_traveler:
        air_traveler = [{"Code": "ADT", "Quantity": 1}]

    return {
        "OTA_AirLowFareSearchRQ": {
            "Version": "5",
            "POS": {
                "Source": [{
                    "PseudoCityCode": "DQ2J",
                    "RequestorID": {
                        "Type": "1",
                        "ID": "1",
                        "CompanyName": {"Code": "TN"},
                    },
                }]
            },
            "OriginDestinationInformation": origin_destinations,
            "TravelPreferences": {
                "MaxStopsQuantity": max_stops,
                "TPA_Extensions": {
                    "VerificationItinCallLogic": {"Value": "L"}
                },
            },
            "TravelerInfoSummary": {
                "AirTravelerAvail": [{"PassengerTypeQuantity": air_traveler}]
            },
            "TPA_Extensions": {
                "IntelliSellTransaction": {
                    "RequestType": {"Name": "50ITINS"}
                }
            },
        }
    }


def revalidar_itinerario(datos):
    """Consulta Sabre Revalidate y devuelve un dict con 'disponible' True/False."""
    tramos = datos.get("tramos") or []
    if not tramos:
        return {
            "disponible": False,
            "error": "Debe enviar al menos un tramo del itinerario",
            "code": 400,
        }

    pasajeros = {
        "adults": datos.get("adults", 1),
        "children": datos.get("children", 0),
        "infants": datos.get("infants", 0),
    }

    try:
        payload = _construir_payload(tramos, pasajeros)
    except (KeyError, TypeError, ValueError) as e:
        return {
            "disponible": False,
            "error": f"Datos del itinerario incompletos: {e}",
            "code": 400,
        }

    try:
        response = _llamar_revalidate(payload)
        if response.status_code == 401:
            response = _llamar_revalidate(payload, force_refresh=True)

        try:
            raw = response.json()
        except ValueError:
            raw = {"raw_response": response.text}

        if response.status_code != 200:
            return {
                "disponible": False,
                "error": "Sabre rechazo la revalidacion",
                "code": response.status_code,
                "detalle": raw,
            }

        grouped = raw.get("groupedItineraryResponse", {}) or {}
        count = (grouped.get("statistics") or {}).get("itineraryCount", 0)
        itinerary_groups = grouped.get("itineraryGroups") or []
        itinerarios = itinerary_groups[0].get("itineraries", []) if itinerary_groups else []

        if not count or not itinerarios:
            return {
                "disponible": False,
                "error": "El vuelo ya no esta disponible para reserva",
                "code": 409,
            }

        first = itinerarios[0]
        pricing = (first.get("pricingInformation") or [{}])[0].get("fare", {})
        total_fare = pricing.get("totalFare", {})

        return {
            "disponible": True,
            "mensaje": "El vuelo sigue disponible",
            "precio_total": total_fare.get("totalPrice"),
            "precio_base": total_fare.get("baseFareAmount"),
            "impuestos": total_fare.get("totalTaxAmount"),
            "moneda": total_fare.get("currency"),
            "ultima_fecha_compra": pricing.get("lastTicketDate"),
            "ultima_hora_compra": pricing.get("lastTicketTime"),
            "aerolinea_validadora": pricing.get("validatingCarrierCode"),
        }

    except (requests.RequestException, SabreAuthError) as e:
        return {"disponible": False, "error": str(e), "code": 500}
