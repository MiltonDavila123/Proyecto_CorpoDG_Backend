import requests
import json

API_KEY = "990c3764-207e-4b58-a688-f04ab95a4588"

def guardar_ciudades():
    print("Obteniendo todas las ciudades...")
    
    response = requests.get(
        "https://airlabs.co/api/v9/cities",
        params={
            "api_key": API_KEY,
            "_fields": "name,city_code,lat,lng,country_code"
        }
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    data = response.json().get("response", [])
    print(f"Total ciudades obtenidas: {len(data)}")

    with open("ciudades.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Guardado en ciudades.json")

    # Muestra las primeras 5 para verificar
    print("\nMuestra:")
    for c in data[:5]:
        print(f"{c.get('city_code')} | {c.get('name')} | {c.get('country_code')} | {c.get('lat')}, {c.get('lng')}")

def cargar_ciudades():
    with open("ciudades.json", "r", encoding="utf-8") as f:
        return json.load(f)

def buscar_ciudades_por_pais(codigo_iso):
    ciudades = cargar_ciudades()
    resultado = [c for c in ciudades if c.get("country_code") == codigo_iso.upper()]
    print(f"\nCiudades en {codigo_iso}: {len(resultado)}")
    for c in resultado:
        print(f"  {c.get('city_code')} | {c.get('name')} | {c.get('lat')}, {c.get('lng')}")
    return resultado

if __name__ == "__main__":
    # PASO 1: Ejecuta esto UNA sola vez
    guardar_ciudades()

    # PASO 2: Despues usa esto para buscar por pais
    # buscar_ciudades_por_pais("EC")  # Ecuador
    # buscar_ciudades_por_pais("MX")  # Mexico