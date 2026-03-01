import requests
import pandas as pd
import json
import time

# --- CONFIGURACIÓN ---
# Coloca tu API Key aquí
API_KEY = 'TU_API_KEY_AQUI' 

# URL del CSV de aeropuertos
URL_CSV_FUENTE = "https://raw.githubusercontent.com/lxndrblz/Airports/main/airports.csv"

# Nombre del archivo donde guardaremos el resultado final
ARCHIVO_SALIDA = "aeropuertos_full_data.json"

def main():
    print(f"🚀 Iniciando el proceso de aeropuertos...")
    
    # 1. Leer el CSV directamente desde la URL usando Pandas
    try:
        print(f"📥 Descargando y leyendo CSV base de GitHub...")
        # Leemos el CSV
        df = pd.read_csv(URL_CSV_FUENTE)
        # Obtenemos solo la columna 'code' (IATA) y la convertimos a una lista simple
        # Nota: Filtramos los que no sean nulos para evitar errores
        lista_codigos = df['code'].dropna().tolist()
        
        print(f"✅ CSV leído: {len(lista_codigos)} aeropuertos para procesar.\n")
    except Exception as e:
        print(f"❌ Error fatal leyendo el CSV: {e}")
        return

    # Lista donde guardaremos los objetos limpios
    resultados_finales = []
    
    # Encabezados para la API Ninjas
    headers = {'X-Api-Key': API_KEY}

    # 2. Recorrer la lista y consultar la API
    # NOTA: Si quieres probar con pocos, cambia 'lista_codigos' por 'lista_codigos[:5]' en la línea de abajo
    for index, codigo_iata in enumerate(lista_codigos):
        
        # Limpiamos espacios en blanco por si acaso
        codigo_iata = str(codigo_iata).strip()

        # Url de consulta a la API de Airports
        url_api = "https://api.api-ninjas.com/v1/airports"
        params = {'iata': codigo_iata}

        try:
            # Hacemos la petición
            response = requests.get(url_api, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificamos si la lista NO está vacía
                if data and len(data) > 0:
                    # Agregamos SOLO el objeto con la info (data[0]) a nuestra lista final
                    # Esto te dará el formato { "iata": "...", "name": "...", ... } que querías
                    aeropuerto_info = data[0]
                    resultados_finales.append(aeropuerto_info)
                    
                    nombre = aeropuerto_info.get('name', 'Desconocido')
                    print(f"[{index+1}/{len(lista_codigos)}] ✅ Encontrado: {nombre} ({codigo_iata})")
                else:
                    print(f"[{index+1}/{len(lista_codigos)}] ⚠️  API devolvió vacío para: {codigo_iata}")
            else:
                print(f"[{index+1}/{len(lista_codigos)}] 🛑 Error {response.status_code} en la API para: {codigo_iata}")

        except requests.exceptions.Timeout:
            print(f"[{index+1}/{len(lista_codigos)}] ⏳ Timeout con: {codigo_iata}")
        except Exception as e:
            print(f"[{index+1}/{len(lista_codigos)}] 💥 Error inesperado con {codigo_iata}: {e}")

        # --- IMPORTANTE ---
        # Pausa para respetar el rate limit de la API
        time.sleep(0.3)

    # 3. Guardar todo en un nuevo JSON
    print(f"\n💾 Guardando {len(resultados_finales)} aeropuertos encontrados en {ARCHIVO_SALIDA}...")
    
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump(resultados_finales, f, indent=4, ensure_ascii=False)
    
    print("🎉 ¡Proceso terminado! Revisa tu archivo JSON.")

if __name__ == "__main__":
    main()