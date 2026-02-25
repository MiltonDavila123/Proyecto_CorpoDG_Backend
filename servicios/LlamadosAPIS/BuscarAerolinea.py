import requests
import json

# 1. TU TOKEN (El que ya tienes, empieza con T1RLAQ...)
TOKEN = "T1RLAQLg6sUPmZpmmVPsUhsRyLRg7PNe7TxKDJ7dsbUAGf9IGxD0Eln/n5+mcx0TjG1uE5nlAADgAO57Sl3w+0U/OROiZcPGL8BfMH5AXDujjFGAbFp98mJNoypVtx2IkQX4d4wU3VE7FjzDaWPRuFNN82HdNhUu2ZNJ7EYT5/hqHC/yFPclNNpr6KjvuCMp8lZN6WM9EqggH9trKvzOex1KfO81ulUWgxeiwfE8kPSDJ3mFfPyF3tD8RNleGwIVWfAfAXBrhWZpCA5Wug6pFOiW241YLvAZLJlmg829J9HRCoPI71Hj8PX7UqUvi1cCnxE/N+xW7m5tyt+q3h35j3XqtnZy1O4fFK9Zsu0tLxOklPjH1FqDVbE*"

# 2. Configuración
# Base URL + El endpoint específico que sale en tu documentación
URL_AEROLINEAS = "https://api.cert.platform.sabre.com/v1/lists/utilities/airlines"

def obtener_nombre_aerolinea(codigo_iata):
    """
    Consulta a Sabre el nombre real de una aerolínea dado su código (Ej: 'AA' -> 'American Airlines')
    """
    
    # Parámetros de la consulta (Query Parameters)
    params = {
        "airlinecode": codigo_iata
        # Ej: "AA" o "AA,AM,IB"
    }

    headers = {
        "Authorization": f"Bearer {TOKEN}"
        # Nota: En peticiones GET no hace falta Content-Type: application/json usualmente
    }

    print(f"🔎 Consultando quién es '{codigo_iata}'...")

    try:
        response = requests.get(URL_AEROLINEAS, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ ¡ENCONTRADO!")
            
            # Sabre devuelve una lista bajo la llave "AirlineInfo"
            lista_aerolineas = data.get("AirlineInfo", [])
            
            for aero in lista_aerolineas:
                codigo = aero.get("AirlineCode")
                nombre = aero.get("AirlineName")
                otro_nombre = aero.get("AlternativeBusinessName")
                print(f"✈️  {codigo} = {nombre} or {otro_nombre}")
                
        else:
            print(f"\n❌ Error {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    # PRUEBA: Buscamos American Airlines (AA) y Aeroméxico (AM)
    # Puedes probar con varios separados por coma
    obtener_nombre_aerolinea("AA,AM,IB,Y4,6G,AV,B6")