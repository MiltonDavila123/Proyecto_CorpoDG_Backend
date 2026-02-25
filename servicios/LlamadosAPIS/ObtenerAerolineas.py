import requests
import json
import time

# --- CONFIGURACIÓN ---
# ¡OJO! Pon aquí tu API Key de API-Ninjas
API_KEY = 'l8uIVJyPNytpFZqd3cBtmw==s50KtvQO4n6aeIfr' 

# URL del JSON base (el que tú me pasaste)
URL_FUENTE = "https://raw.githubusercontent.com/BesrourMS/Airlines/refs/heads/master/airlines.json"

# Nombre del archivo donde guardaremos el resultado final
ARCHIVO_SALIDA = "aerolineas_full_data.json"

def main():
    print(f"🚀 Iniciando el proceso locochón...")
    
    # 1. Descargar la lista semilla desde GitHub
    try:
        print(f"📥 Descargando lista base de GitHub...")
        response_fuente = requests.get(URL_FUENTE)
        lista_base = response_fuente.json()
        print(f"✅ Lista base obtenida: {len(lista_base)} aerolíneas para procesar.\n")
    except Exception as e:
        print(f"❌ Error fatal descargando la lista base: {e}")
        return

    # Lista donde guardaremos los resultados exitosos
    resultados_finales = []
    
    # Encabezados para la API Ninjas
    headers = {'X-Api-Key': API_KEY}

    # 2. Recorrer la lista y consultar la API
    for index, aerolinea in enumerate(lista_base):
        codigo_iata = aerolinea.get('code') # Obtenemos el código "X4", "AA", etc.
        nombre_base = aerolinea.get('name', 'Desconocida')

        # Si no hay código, saltamos
        if not codigo_iata:
            continue

        # Url de consulta a la API
        url_api = f"https://api.api-ninjas.com/v1/airlines?iata={codigo_iata}"

        try:
            # Hacemos la petición con un timeout de 5 segundos para que no se trabe
            response = requests.get(url_api, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificamos si la lista NO está vacía
                if data and len(data) > 0:
                    # Agregamos los datos encontrados a nuestra lista final
                    # data[0] toma el primer resultado que suele ser el correcto
                    resultados_finales.append(data[0]) 
                    print(f"[{index+1}/{len(lista_base)}] ✅ Encontrada: {nombre_base} ({codigo_iata})")
                else:
                    print(f"[{index+1}/{len(lista_base)}] ⚠️  API devolvió vacío para: {codigo_iata}")
            else:
                print(f"[{index+1}/{len(lista_base)}] 🛑 Error {response.status_code} en la API para: {codigo_iata}")

        except requests.exceptions.Timeout:
            print(f"[{index+1}/{len(lista_base)}] ⏳ Timeout (se tardó mucho) con: {codigo_iata}")
        except Exception as e:
            print(f"[{index+1}/{len(lista_base)}] 💥 Error inesperado con {codigo_iata}: {e}")

        # --- IMPORTANTE ---
        # Dormimos el script un poquito (0.2 seg) para no saturar la API y que no nos bloqueen
        # Si tienes una cuenta gratis, quizás quieras subir esto a 0.5 o 1.0
        time.sleep(0.2)

    # 3. Guardar todo en un nuevo JSON
    print(f"\n💾 Guardando {len(resultados_finales)} aerolíneas encontradas en {ARCHIVO_SALIDA}...")
    
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump(resultados_finales, f, indent=4, ensure_ascii=False)
    
    print("🎉 ¡Proceso terminado! Revisa tu archivo nuevo.")

if __name__ == "__main__":
    main()