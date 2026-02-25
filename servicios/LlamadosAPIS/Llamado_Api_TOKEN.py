import base64
import requests

def obtener_token_sabre_v1():
    # TUS CREDENCIALES
    client_id = "V1:9tho7sxqg11a3rb7:DEVCENTER:EXT"
    client_secret = "pG9hBVv4"
    
    # URL
    url = "https://api.cert.platform.sabre.com/v2/auth/token"

    # PASO 1: Codificar Client ID (User)
    # YAML: base64(V1:user:group:domain)
    b64_client_id = base64.b64encode(client_id.encode('ascii')).decode('ascii')
    
    # PASO 2: Codificar Client Secret (Password)
    # YAML: base64(password)
    b64_client_secret = base64.b64encode(client_secret.encode('ascii')).decode('ascii')
    
    # PASO 3: Concatenar con dos puntos
    concatenated = f"{b64_client_id}:{b64_client_secret}"
    
    # PASO 4: Codificar TODO de nuevo
    # YAML: base64( ... : ... )
    final_auth_string = base64.b64encode(concatenated.encode('ascii')).decode('ascii')
    
    # Imprimir para depurar (Debería coincidir con el token largo de arriba)
    # print(f"Cadena generada: {final_auth_string}")

    headers = {
        "Authorization": f"Basic {final_auth_string}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Sabre Auth Error: {response.text}")

# Probar
try:
    token = obtener_token_sabre_v1()
    print(f"✅ Token obtenido: {token}")
    
    # Guardar el token en un archivo
    with open('sabre_token.txt', 'w') as f:
        f.write(f"Token de Sabre API\n")
        f.write(f"===================\n\n")
        f.write(f"Token: {token}\n\n")
        f.write(f"Nota: Este token expira. Vuelve a ejecutar el script si necesitas uno nuevo.\n")
    print("💾 Token guardado en: sabre_token.txt")
    
except Exception as e:
    print(f"❌ {e}")