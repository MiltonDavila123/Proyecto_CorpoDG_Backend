from datetime import datetime, timedelta

import requests
from .LlamadosAPIS.Llamado_Api_TOKEN import SabreAuthError, obtener_token_sabre

SABRE_URL = "https://api.cert.platform.sabre.com/v5/offers/shop" 
PROVEEDOR_SABRE = "sabre"


def _construir_ids_fuente(proveedor, id_itinerario, indice):
    proveedor_normalizado = (proveedor or "desconocido").lower()
    id_fuente = str(id_itinerario) if id_itinerario is not None else f"idx-{indice}"
    id_unico = f"{proveedor_normalizado}:{id_fuente}"
    return proveedor_normalizado, id_fuente, id_unico


def _buscar_en_sabre(payload, force_refresh=False):
    token = obtener_token_sabre(force_refresh=force_refresh)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return requests.post(SABRE_URL, headers=headers, json=payload, timeout=30)

def buscar_vuelos_sabre(datos):
   
    origen = datos.get('origin')
    destino = datos.get('destination')
    fecha_ida = datos.get('date')
    fecha_vuelta = datos.get('return_date')
    
    # --- LÍMITE DE RESULTADOS (default 20, máximo 200) ---
    limit = min(int(datos.get('limit', 20)), 200)
    if limit <= 50:
        request_type = "50ITINS"
    elif limit <= 100:
        request_type = "100ITINS"
    else:
        request_type = "200ITINS"
    
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
                    "NumTrips": {"Number": limit}
                }
            },
            "TravelerInfoSummary": {
                "AirTravelerAvail": [{
                    "PassengerTypeQuantity": pasajeros
                }]
            },
            "TPA_Extensions": {
                "IntelliSellTransaction": {
                    "RequestType": {"Name": request_type}
                }
            }
        }
    }

    try:
        response = _buscar_en_sabre(payload)

       
        if response.status_code == 401:
            response = _buscar_en_sabre(payload, force_refresh=True)

        try:
            raw_response = response.json()
        except ValueError:
            raw_response = {"raw_response": response.text}

        if response.status_code != 200:
            return {
                "error": "Error en Sabre",
                "code": response.status_code,
                "detail": raw_response
            }

        return procesar_respuesta(raw_response, proveedor=PROVEEDOR_SABRE)

    except (requests.RequestException, SabreAuthError, ValueError) as e:
        return {"error": str(e), "code": 500}

def formatear_duracion(minutos):
    """Convierte minutos a formato legible (ej: 2h 30m)"""
    horas = minutos // 60
    mins = minutos % 60
    return f"{horas}h {mins}m"

def procesar_respuesta(data_json, proveedor=PROVEEDOR_SABRE):
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
        mapa_fare_descs = {fc['id']: fc for fc in resp.get('fareComponentDescs', [])}

        # Fechas de cada tramo (leg) segun lo solicitado en la busqueda
        leg_descriptions = itinerary_groups[0].get('groupDescription', {}).get('legDescriptions', [])

        itinerarios = itinerary_groups[0].get('itineraries', [])

        for idx_itinerario, it in enumerate(itinerarios, start=1):
            fare = it['pricingInformation'][0]['fare']['totalFare']
            pricing_info = it['pricingInformation'][0]['fare']

            # Construir lista de fareComponents con su bookingCode representativo.
            # IMPORTANTE: dentro de un fareComponent, todos los vuelos comparten la
            # misma clase. Adicionalmente, fareComponents[].segments puede traer
            # entradas vacias (surface/hidden) que NO corresponden a schedules, por
            # eso NO se puede mapear secuencialmente. Se mapea por rango
            # beginAirport -> endAirport contra los schedules reales.
            fare_components_info = []
            passenger_info_list = pricing_info.get('passengerInfoList') or []
            if passenger_info_list:
                passenger_info = passenger_info_list[0].get('passengerInfo', {})
                for fc in passenger_info.get('fareComponents', []):
                    code = None
                    cabin = None
                    for seg in fc.get('segments', []):
                        seg_data = seg.get('segment') or {}
                        if not code and seg_data.get('bookingCode'):
                            code = seg_data.get('bookingCode')
                        if not cabin and seg_data.get('cabinCode'):
                            cabin = seg_data.get('cabinCode')
                        if code and cabin:
                            break
                    # Datos del fareComponentDescs referenciado (fareBasis, etc.)
                    fc_desc = mapa_fare_descs.get(fc.get('ref'), {})
                    fare_components_info.append({
                        'begin': fc.get('beginAirport'),
                        'end': fc.get('endAirport'),
                        'code': code,
                        'cabin': cabin or fc_desc.get('cabinCode'),
                        'fare_basis': fc_desc.get('fareBasisCode'),
                        'governing_carrier': fc_desc.get('governingCarrier'),
                        'brand_code': fc.get('brandCode') or fc_desc.get('brandCode'),
                        'fare_amount': fc_desc.get('fareAmount'),
                        'fare_currency': fc_desc.get('fareCurrency'),
                    })
            fc_idx = 0
            id_original = it.get('id')
            proveedor_actual, id_fuente, id_unico = _construir_ids_fuente(
                proveedor,
                id_original,
                idx_itinerario
            )
            
            opcion = {
                "id": id_original,
                "proveedor": proveedor_actual,
                "id_itinerario_proveedor": id_fuente,
                "id_itinerario_unico": id_unico,
                "precio_total": fare.get('totalPrice'),
                "precio_base": fare.get('baseFareAmount'),
                "impuestos": fare.get('totalTaxAmount'),
                "moneda": fare.get('currency'),
                "aerolinea_validadora": pricing_info.get('validatingCarrierCode'),
                "ultima_fecha_compra": pricing_info.get('lastTicketDate'),
                "fare_info": [
                    {
                        "begin": fci['begin'],
                        "end": fci['end'],
                        "fare_basis": fci['fare_basis'],
                        "governing_carrier": fci['governing_carrier'],
                        "brand_code": fci['brand_code'],
                        "cabin": fci['cabin'],
                        "booking_code": fci['code'],
                        "fare_amount": fci['fare_amount'],
                        "fare_currency": fci['fare_currency'],
                    }
                    for fci in fare_components_info
                ],
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

                # Fecha base del tramo (desde la propia respuesta de Sabre)
                fecha_tramo_str = None
                if idx < len(leg_descriptions):
                    fecha_tramo_str = leg_descriptions[idx].get('departureDate')
                try:
                    fecha_actual = datetime.strptime(fecha_tramo_str, "%Y-%m-%d").date() if fecha_tramo_str else None
                except (TypeError, ValueError):
                    fecha_actual = None

                tramo = {
                    "tipo": tipo_tramo,
                    "fecha_salida": fecha_tramo_str,
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

                    dep_time_raw = segmento_data.get('departure', {}).get('time', '') or ''
                    arr_time_raw = segmento_data.get('arrival', {}).get('time', '') or ''
                    dep_time = dep_time_raw[:8] if len(dep_time_raw) >= 8 else dep_time_raw
                    arr_time = arr_time_raw[:8] if len(arr_time_raw) >= 8 else arr_time_raw
                    arr_adj = segmento_data.get('arrival', {}).get('dateAdjustment', 0) or 0

                    fecha_hora_salida = None
                    fecha_hora_llegada = None
                    fecha_salida_seg = None
                    fecha_llegada_seg = None
                    if fecha_actual is not None:
                        fecha_salida_seg = fecha_actual
                        fecha_llegada_seg = fecha_actual + timedelta(days=arr_adj)
                        if dep_time:
                            fecha_hora_salida = f"{fecha_salida_seg.isoformat()}T{dep_time}"
                        if arr_time:
                            fecha_hora_llegada = f"{fecha_llegada_seg.isoformat()}T{arr_time}"
                        # El proximo segmento empieza desde la fecha de llegada (aprox)
                        fecha_actual = fecha_llegada_seg

                    clase_servicio = None
                    cabina = None
                    fare_basis_seg = None
                    if fc_idx < len(fare_components_info):
                        clase_servicio = fare_components_info[fc_idx].get('code')
                        cabina = fare_components_info[fc_idx].get('cabin')
                        fare_basis_seg = fare_components_info[fc_idx].get('fare_basis')
                        # Avanzar al siguiente fareComponent cuando este segmento
                        # llega al endAirport del fareComponent actual.
                        arrival_airport = segmento_data.get('arrival', {}).get('airport')
                        if arrival_airport and arrival_airport == fare_components_info[fc_idx].get('end'):
                            fc_idx += 1

                    segmento = {
                        "numero_segmento": seg_idx + 1,
                        "vuelo": f"{carrier.get('marketing', '')}{carrier.get('marketingFlightNumber', '')}",
                        "numero_vuelo": carrier.get('marketingFlightNumber'),
                        "numero_vuelo_operador": carrier.get('operatingFlightNumber') or carrier.get('marketingFlightNumber'),
                        "clase_servicio": clase_servicio,
                        "cabina": cabina,
                        "fare_basis": fare_basis_seg,
                        "fecha_salida": fecha_salida_seg.isoformat() if fecha_salida_seg else None,
                        "fecha_llegada": fecha_llegada_seg.isoformat() if fecha_llegada_seg else None,
                        "fecha_hora_salida": fecha_hora_salida,
                        "fecha_hora_llegada": fecha_hora_llegada,
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

        # --- ORDENAR: menor escalas → menor duración → menor precio ---
        def sort_key(opcion):
            total_escalas = sum(t.get('numero_escalas', 0) for t in opcion.get('tramos', []))
            total_duracion = sum(t.get('duracion_minutos', 0) for t in opcion.get('tramos', []))
            precio = opcion.get('precio_total') or 0
            return (total_escalas, total_duracion, precio)
        
        resultados.sort(key=sort_key)
        
        return resultados
    except (KeyError, TypeError, ValueError, IndexError) as e:  # pylint: disable=broad-exception-caught
        return {"error": f"Error procesando respuesta: {str(e)}"}