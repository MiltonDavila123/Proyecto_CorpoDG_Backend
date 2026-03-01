import requests
import json
from django.conf import settings

SABRE_URL = "https://api.cert.platform.sabre.com/v5/offers/shop" 

def buscar_vuelos_sabre(datos):
    # --- EXTRACCIÓN DE VARIABLES ---
    origen = datos.get('origin')
    destino = datos.get('destination')
    fecha_ida = datos.get('date')
    fecha_vuelta = datos.get('return_date')
    
    # --- LÓGICA DE TRAMOS (IDA O IDA/VUELTA) ---
    tramos = [
        {
            "RPH": "1",
            "DepartureDateTime": f"{fecha_ida}T00:00:00",
            "OriginLocation": {"LocationCode": origen},
            "DestinationLocation": {"LocationCode": destino}
        }
    ]
    if fecha_vuelta:
        tramos.append({
            "RPH": "2",
            "DepartureDateTime": f"{fecha_vuelta}T00:00:00",
            "OriginLocation": {"LocationCode": destino},
            "DestinationLocation": {"LocationCode": origen}
        })

    # --- LÓGICA DE PASAJEROS ---
    pasajeros = []
    if int(datos.get('adults', 0)) > 0:
        pasajeros.append({"Code": "ADT", "Quantity": int(datos['adults'])})
    if int(datos.get('children', 0)) > 0:
        pasajeros.append({"Code": "CNN", "Quantity": int(datos['children'])})
    if int(datos.get('infants', 0)) > 0:
        pasajeros.append({"Code": "INF", "Quantity": int(datos['infants'])})

    # --- ESTRUCTURA EXACTA REQUERIDA ---
    payload = {
        "OTA_AirLowFareSearchRQ": {
            "Version": "5",
            "POS": {
                "Source": [{
                    "PseudoCityCode": "DQ2J",
                    "RequestorID": {
                        "Type": "1",
                        "ID": "1",
                        "CompanyName": {"Code": "TN"}
                    }
                }]
            },
            "OriginDestinationInformation": tramos,
            "TravelPreferences": {
                "CabinPref": [{
                    "Cabin": datos.get('cabin_class', 'Y'), 
                    "PreferLevel": "Preferred"
                }],
                "TPA_Extensions": {
                    "NumTrips": {"Number": 20}
                }
            },
            "TravelerInfoSummary": {
                "AirTravelerAvail": [{
                    "PassengerTypeQuantity": pasajeros
                }]
            },
            "TPA_Extensions": {
                "IntelliSellTransaction": {
                    "RequestType": {"Name": "50ITINS"}
                }
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(SABRE_URL, headers=headers, json=payload, timeout=30)
        raw_response = response.json()

        if response.status_code != 200:
            return {"error": "Error en Sabre", "detail": raw_response}

        return procesar_respuesta(raw_response)

    except Exception as e:
        return {"error": str(e)}

def formatear_duracion(minutos):
    """Convierte minutos a formato legible (ej: 2h 30m)"""
    horas = minutos // 60
    mins = minutos % 60
    return f"{horas}h {mins}m"

def procesar_respuesta(data_json):
    """Devuelve un JSON limpio y ordenado para el Frontend"""
    try:
        resultados = []
        resp = data_json.get('groupedItineraryResponse', {})
        itinerary_groups = resp.get('itineraryGroups', [])

        if not itinerary_groups:
            return []

        # Mapas de referencias
        mapa_schedules = {sch['id']: sch for sch in resp.get('scheduleDescs', [])}
        mapa_legs = {leg['id']: leg for leg in resp.get('legDescs', [])}
        
        itinerarios = itinerary_groups[0].get('itineraries', [])

        for it in itinerarios:
            fare = it['pricingInformation'][0]['fare']['totalFare']
            pricing_info = it['pricingInformation'][0]['fare']
            
            opcion = {
                "id": it.get('id'),
                "precio_total": fare.get('totalPrice'),
                "precio_base": fare.get('baseFareAmount'),
                "impuestos": fare.get('totalTaxAmount'),
                "moneda": fare.get('currency'),
                "aerolinea_validadora": pricing_info.get('validatingCarrierCode'),
                "ultima_fecha_compra": pricing_info.get('lastTicketDate'),
                "tramos": []
            }

            legs_list = it.get('legs', [])
            for idx, leg_ref in enumerate(legs_list):
                # Buscar el legDesc correspondiente
                leg_data = mapa_legs.get(leg_ref['ref'], {})
                schedules = leg_data.get('schedules', [])
                
                if not schedules:
                    continue
                
                # Información del primer y último segmento
                primer_segmento = mapa_schedules.get(schedules[0]['ref'], {})
                ultimo_segmento = mapa_schedules.get(schedules[-1]['ref'], {})
                
                num_escalas = len(schedules) - 1
                duracion_total = leg_data.get('elapsedTime', 0)
                
                # Determinar tipo de tramo
                tipo_tramo = "ida" if idx == 0 else "vuelta"
                
                tramo = {
                    "tipo": tipo_tramo,
                    "origen": {
                        "aeropuerto": primer_segmento.get('departure', {}).get('airport', ''),
                        "ciudad": primer_segmento.get('departure', {}).get('city', ''),
                        "pais": primer_segmento.get('departure', {}).get('country', ''),
                        "hora": primer_segmento.get('departure', {}).get('time', '')
                    },
                    "destino": {
                        "aeropuerto": ultimo_segmento.get('arrival', {}).get('airport', ''),
                        "ciudad": ultimo_segmento.get('arrival', {}).get('city', ''),
                        "pais": ultimo_segmento.get('arrival', {}).get('country', ''),
                        "hora": ultimo_segmento.get('arrival', {}).get('time', '')
                    },
                    "duracion_total": formatear_duracion(duracion_total),
                    "duracion_minutos": duracion_total,
                    "tiene_escalas": num_escalas > 0,
                    "numero_escalas": num_escalas,
                    "segmentos": []
                }
                
                # Procesar cada segmento del tramo
                for seg_idx, schedule_ref in enumerate(schedules):
                    segmento_data = mapa_schedules.get(schedule_ref['ref'], {})
                    carrier = segmento_data.get('carrier', {})
                    
                    segmento = {
                        "numero_segmento": seg_idx + 1,
                        "vuelo": f"{carrier.get('marketing', '')}{carrier.get('marketingFlightNumber', '')}",
                        "aerolinea": {
                            "codigo": carrier.get('marketing', ''),
                            "operada_por": carrier.get('operating', ''),
                            "nombre_compartido": carrier.get('codeShared', ''),
                            "alianza": carrier.get('alliances', '').strip() if carrier.get('alliances') else None
                        },
                        "salida": {
                            "aeropuerto": segmento_data.get('departure', {}).get('airport', ''),
                            "ciudad": segmento_data.get('departure', {}).get('city', ''),
                            "pais": segmento_data.get('departure', {}).get('country', ''),
                            "hora": segmento_data.get('departure', {}).get('time', ''),
                            "terminal": segmento_data.get('departure', {}).get('terminal')
                        },
                        "llegada": {
                            "aeropuerto": segmento_data.get('arrival', {}).get('airport', ''),
                            "ciudad": segmento_data.get('arrival', {}).get('city', ''),
                            "pais": segmento_data.get('arrival', {}).get('country', ''),
                            "hora": segmento_data.get('arrival', {}).get('time', ''),
                            "terminal": segmento_data.get('arrival', {}).get('terminal'),
                            "dia_siguiente": segmento_data.get('arrival', {}).get('dateAdjustment', 0) > 0
                        },
                        "duracion": formatear_duracion(segmento_data.get('elapsedTime', 0)),
                        "duracion_minutos": segmento_data.get('elapsedTime', 0),
                        "millas": segmento_data.get('totalMilesFlown', 0),
                        "avion": segmento_data.get('carrier', {}).get('equipment', {}).get('code', ''),
                        "paradas_intermedias": segmento_data.get('stopCount', 0)
                    }
                    tramo["segmentos"].append(segmento)
                
                # Agregar info de escalas si las hay
                if num_escalas > 0:
                    escalas_info = []
                    for i in range(num_escalas):
                        seg_actual = mapa_schedules.get(schedules[i]['ref'], {})
                        seg_siguiente = mapa_schedules.get(schedules[i + 1]['ref'], {})
                        
                        escala = {
                            "aeropuerto": seg_actual.get('arrival', {}).get('airport', ''),
                            "ciudad": seg_actual.get('arrival', {}).get('city', ''),
                            "pais": seg_actual.get('arrival', {}).get('country', ''),
                            "hora_llegada": seg_actual.get('arrival', {}).get('time', ''),
                            "hora_salida": seg_siguiente.get('departure', {}).get('time', '')
                        }
                        escalas_info.append(escala)
                    tramo["escalas"] = escalas_info
                
                opcion["tramos"].append(tramo)
            
            # Resumen rápido de aerolíneas
            aerolineas_ida = set()
            aerolineas_vuelta = set()
            for tramo in opcion["tramos"]:
                for seg in tramo["segmentos"]:
                    if tramo["tipo"] == "ida":
                        aerolineas_ida.add(seg["aerolinea"]["codigo"])
                    else:
                        aerolineas_vuelta.add(seg["aerolinea"]["codigo"])
            
            opcion["resumen"] = {
                "aerolineas_ida": list(aerolineas_ida),
                "aerolineas_vuelta": list(aerolineas_vuelta),
                "es_vuelo_directo_ida": len(opcion["tramos"]) > 0 and not opcion["tramos"][0].get("tiene_escalas", True),
                "es_vuelo_directo_vuelta": len(opcion["tramos"]) > 1 and not opcion["tramos"][1].get("tiene_escalas", True)
            }
            
            resultados.append(opcion)

        return resultados
    except Exception as e:
        return {"error": f"Error procesando respuesta: {str(e)}"}