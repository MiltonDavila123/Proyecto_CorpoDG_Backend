import requests
import json

# TU TOKEN
TOKEN = "T1RLAQI4XtePmD8FbNxKCuUhpM/cPm25Cbouwr9+Gsxocm3MVxBvEDbkuHocad3fWzCcGVM+AADgFtZv8IiaYiA22rGflTio3JfPqslfYJihZplcFAzKlp0YeSuS0qC2DnpqW/38JO249HTSz2SWTk+ndUgoyPM4gBI6O+JRYRxElYar/S1zbdhlrySp8B21NVXmon13QIQLfUxSdOIWk1hzCTfiE+t50o/R00N0kURGeMLL57A4uLeOjC8ADH5yvt9utJ7/MSwHdt1Hsem5Q7ViSu6ZrPJU2Vquo7yw8FDDcH2aXFzp4sDxme/TDYGEIiGvE2uKToQOu57iJoQN2Nt/Mr0x8rTUJQEFh34/9SPSoCx3kZEdN5g*" 

# URLS
URL_MAC = "https://api.cert.platform.sabre.com/v1/lists/supported/cities"
# ⚠️ CAMBIO: Usamos la API de Autocompletado que es más potente
URL_AUTOCOMPLETE = "https://api.cert.platform.sabre.com/v1/geo/autocomplete"

def obtener_info_lugar_robusto(codigo):
    codigo = codigo.upper()
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print(f"🔎 Analizando '{codigo}'...")

    # --- PASO 1: ¿Es una Ciudad Multi-Aeropuerto (MAC)? (Como LON, NYC) ---
    try:
        url_mac = f"{URL_MAC}/{codigo}/airports"
        response_mac = requests.get(url_mac, headers=headers)
        
        if response_mac.status_code == 200:
            data = response_mac.json()
            print(f"✅ '{codigo}' es una Ciudad con Varios Aeropuertos:")
            aeropuertos = data.get("Airports", [])
            for aero in aeropuertos:
                print(f"   🏙️  Hijo: [{aero['code']}] - {aero['name']}")
            return # Terminamos aquí si tuvo éxito
    except Exception:
        pass 

    # --- PASO 2: Intentar con Geo Autocomplete (Para UIO, CUN, etc.) ---
    print(f"⚠️ No es MAC. Buscando en Geo Autocomplete...")
    
    try:
        params = {
            "query": codigo,
            "category": "AIR", # Solo aeropuertos
            "limit": 3
        }
        response_geo = requests.get(URL_AUTOCOMPLETE, headers=headers, params=params)
        
        if response_geo.status_code == 200:
            data = response_geo.json()
            
            # La estructura de Autocomplete suele ser: Response -> docs -> lista
            docs = data.get("Response", {}).get("docs", [])
            
            if docs:
                print(f"✅ ¡ENCONTRADO EN AUTOCOMPLETE!")
                for lugar in docs:
                    # A veces el campo es 'id' o 'city' dependiendo de la version
                    code = lugar.get('id', '???')
                    name = lugar.get('name', '???')
                    print(f"   ✈️  [{code}] - {name}")
            else:
                print("❌ Autocomplete respondió 200 OK pero lista vacía (El entorno Test está vacío para esto).")
                
        else:
             print(f"❌ Error en Autocomplete: {response_geo.status_code}")
             # Si da 403 o 404 es que tu usuario de prueba no tiene acceso a esta API específica
             print(response_geo.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("-" * 40)
    obtener_info_lugar_robusto("LON") # Debería salir por Paso 1
    
    print("-" * 40)
    obtener_info_lugar_robusto("UIO") # Debería salir por Paso 2
    
    print("-" * 40)
    obtener_info_lugar_robusto("CUN") # Debería salir por Paso 2