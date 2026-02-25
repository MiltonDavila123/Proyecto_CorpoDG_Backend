import requests
import json

REGIONES = ["africa", "americas", "asia", "europe", "oceania"]

def guardar_paises_por_region():
    resultado = {}

    for region in REGIONES:
        print(f"Obteniendo {region}...")
        response = requests.get(f"https://www.apicountries.com/region/{region}")

        if response.status_code != 200:
            print(f"  Error en {region}: {response.status_code}")
            resultado[region] = []
            continue

        paises = response.json()

        resultado[region] = [
            {
                "nombre_es": p.get("translations", {}).get("es") or p.get("name"),
                "nombre_en": p.get("name"),
                "codigo_iso": p.get("alpha2Code"),
                "codigo_iso3": p.get("alpha3Code"),
                "capital": p.get("capital"),
                "bandera_png": p.get("flags", {}).get("png"),
                "bandera_svg": p.get("flags", {}).get("svg"),
            }
            for p in paises
        ]

        print(f"  {len(resultado[region])} paises en {region}")

    with open("paises_por_region.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print("\nGuardado en paises_por_region.json")

if __name__ == "__main__":
    guardar_paises_por_region()