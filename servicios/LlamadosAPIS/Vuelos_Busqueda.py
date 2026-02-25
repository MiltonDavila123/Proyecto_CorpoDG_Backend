import requests
import json

TOKEN = "T1RLAQI4XtePmD8FbNxKCuUhpM/cPm25Cbouwr9+Gsxocm3MVxBvEDbkuHocad3fWzCcGVM+AADgFtZv8IiaYiA22rGflTio3JfPqslfYJihZplcFAzKlp0YeSuS0qC2DnpqW/38JO249HTSz2SWTk+ndUgoyPM4gBI6O+JRYRxElYar/S1zbdhlrySp8B21NVXmon13QIQLfUxSdOIWk1hzCTfiE+t50o/R00N0kURGeMLL57A4uLeOjC8ADH5yvt9utJ7/MSwHdt1Hsem5Q7ViSu6ZrPJU2Vquo7yw8FDDcH2aXFzp4sDxme/TDYGEIiGvE2uKToQOu57iJoQN2Nt/Mr0x8rTUJQEFh34/9SPSoCx3kZEdN5g*"

URL_BFM = "https://api.cert.platform.sabre.com/v5/offers/shop"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload_A = {
    "OTA_AirLowFareSearchRQ": {
        "Version": "5",
        "POS": {
            "Source": [
                {
                    "PseudoCityCode": "DQ2J",
                    "RequestorID": {
                        "Type": "1",
                        "ID": "1",
                        "CompanyName": {"Code": "TN"}
                    }
                }
            ]
        },
        "OriginDestinationInformation": [
            {
                "RPH": "1",
                "DepartureDateTime": "2026-09-13T00:00:00",
                "OriginLocation": {"LocationCode": "UIO"},
                "DestinationLocation": {"LocationCode": "GYE"}
            },
            {
                "RPH": "2",
                "DepartureDateTime": "2026-09-20T00:00:00",
                "OriginLocation": {"LocationCode": "UIO"},
                "DestinationLocation": {"LocationCode": "GYE"}
            }
        ],
        "TravelPreferences": {
            "MaxStopsQuantity": 0,
            "VendorPref": [{"Code": "LO"}],
            "TPA_Extensions": {
                "NumTrips": {"Number": 50}
            }
        },
        "TravelerInfoSummary": {
            "AirTravelerAvail": [
                {
                    "PassengerTypeQuantity": [
                        {"Code": "ADT", "Quantity": 1}
                    ]
                }
            ]
        },
        "TPA_Extensions": {
            "IntelliSellTransaction": {
                "RequestType": {"Name": "50ITINS"}
            }
        }
    }
}

payload_B = {
    "OTA_AirLowFareSearchRQ": {
        "Version": "5",
        "POS": {
            "Source": [
                {
                    "PseudoCityCode": "DQ2J",
                    "RequestorID": {
                        "Type": "1",
                        "ID": "1",
                        "CompanyName": {"Code": "TN"}
                    }
                }
            ]
        },
        "OriginDestinationInformation": [
            {
                "RPH": "1",
                "DepartureDateTime": "2026-09-11T00:00:00",
                "OriginLocation": {"LocationCode": "UIO"},
                "DestinationLocation": {"LocationCode": "GYE"}
            },
            {
                "RPH": "2",
                "DepartureDateTime": "2026-09-18T00:00:00",
                "OriginLocation": {"LocationCode": "UIO"},
                "DestinationLocation": {"LocationCode": "GYE"}
            }
        ],
        "TravelPreferences": {
            "TPA_Extensions": {
                "NumTrips": {"Number": 50}
            }
        },
        "TravelerInfoSummary": {
            "AirTravelerAvail": [
                {
                    "PassengerTypeQuantity": [
                        {"Code": "ADT", "Quantity": 1}
                    ]
                }
            ]
        },
        "TPA_Extensions": {
            "IntelliSellTransaction": {
                "RequestType": {"Name": "50ITINS"}
            }
        }
    }
}


def buscar(nombre, payload):
    print(f"\n{'='*55}")
    print(f"  PROBANDO {nombre}")
    print(f"{'='*55}")

    response = requests.post(URL_BFM, headers=headers, json=payload)
    print(f"  Status: {response.status_code}")

    if response.status_code == 401:
        print("  Token expirado. Genera uno nuevo.")
        return

    if response.status_code != 200:
        print(f"  Error inesperado:")
        print(response.text)
        return

    data = response.json()
    resp = data.get('groupedItineraryResponse', {})

    mensajes = resp.get('messages', [])
    errores = [m for m in mensajes if m.get('severity') in ('Error', 'Warning')]
    if errores:
        print("  Mensajes de Sabre:")
        for m in errores:
            print(f"     [{m['severity']}] {m['text']}")

    grupos = resp.get('itineraryGroups', [])
    count = resp.get('statistics', {}).get('itineraryCount', 0)

    if count == 0 or not grupos:
        print(f"\n  Sin resultados (itineraryCount={count})")
        print("  Revisa los mensajes de error arriba")
        return

    itinerarios = grupos[0].get('itineraries', [])
    print(f"\n  ✅ {len(itinerarios)} OPCIONES ENCONTRADAS\n")

    schedule_descs = {s['id']: s for s in resp.get('scheduleDescs', [])}
    leg_descs = {l['id']: l for l in resp.get('legDescs', [])}

    # MOSTRAR TODOS LOS VUELOS CON INFORMACIÓN COMPLETA
    for i, it in enumerate(itinerarios):
        fare = it['pricingInformation'][0]['fare']
        total_info = fare['totalFare']
        aerolinea = fare['validatingCarrierCode']
        total = total_info['totalPrice']
        moneda = total_info['currency']
        base_pln = total_info.get('baseFareAmount', '?')
        base_cur = total_info.get('baseFareCurrency', '')
        taxes = total_info.get('totalTaxAmount', '?')

        print(f"{'='*90}")
        print(f"  🎫 OPCIÓN #{i+1}")
        print(f"{'='*90}")
        print(f"  ✈️  AEROLÍNEA VALIDANTE: {aerolinea}")
        print(f"  💰 PRECIO TOTAL: {total} {moneda}")
        print(f"  💵 Tarifa Base: {base_pln} {base_cur}")
        print(f"  🏦 Impuestos: {taxes} {moneda}")
        print(f"  {'─'*90}")

        leg_refs = [l['ref'] for l in it.get('legs', [])]
        for leg_idx, leg_ref in enumerate(leg_refs):
            leg = leg_descs.get(leg_ref, {})
            print(f"\n  🛫 TRAMO {leg_idx + 1}: ")
            
            schedules = leg.get('schedules', [])
            for seg_idx, sch_ref in enumerate(schedules):
                sch = schedule_descs.get(sch_ref['ref'], {})
                dep = sch.get('departure', {})
                arr = sch.get('arrival', {})
                carrier = sch.get('carrier', {})
                
                # Información del vuelo
                marketing_airline = carrier.get('marketing', '?')
                operating_airline = carrier.get('operating', '?')
                flight_number = carrier.get('marketingFlightNumber', '?')
                flight = f"{marketing_airline}{flight_number}"
                
                # Aeropuertos y horarios
                origin = dep.get('airport', '?')
                destination = arr.get('airport', '?')
                dep_time = dep.get('time', '?')
                arr_time = arr.get('time', '?')
                elapsed = sch.get('elapsedTime', '?')
                
                # Información adicional
                cabin = sch_ref.get('cabin', '?')
                booking_class = sch_ref.get('bookingClass', '?')
                equipment = sch.get('equipment', '?')
                meal = sch.get('meals', '?')
                
                print(f"\n     └─ SEGMENTO {seg_idx + 1}:")
                print(f"        Vuelo: {flight}  (Operado por: {operating_airline})")
                print(f"        Origen: {origin} → Destino: {destination}")
                print(f"        Salida: {dep_time}")
                print(f"        Llegada: {arr_time}")
                print(f"        Duración: {elapsed} minutos")
                print(f"        Cabina: {cabin} | Clase: {booking_class}")
                print(f"        Avión: {equipment}")
                if meal != '?':
                    print(f"        Comidas: {meal}")
                
                # Información de escalas
                if seg_idx < len(schedules) - 1:
                    next_sch_ref = schedules[seg_idx + 1]
                    next_sch = schedule_descs.get(next_sch_ref['ref'], {})
                    next_dep = next_sch.get('departure', {})
                    next_dep_time = next_dep.get('time', '?')
                    
                    # Calcular tiempo de escala si es posible
                    print(f"        ⏱️  ESCALA EN {destination} - Próxima salida: {next_dep_time}")
        
        print(f"\n{'='*90}\n")


if __name__ == "__main__":
    buscar("OPCION A - LOT directo, fechas domingo 13/20 sep", payload_A)
    buscar("OPCION B - Cualquier aerolinea, fechas originales 11/18 sep", payload_B)