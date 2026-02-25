import requests
import csv
import io

URL = "https://raw.githubusercontent.com/lxndrblz/Airports/main/airports.csv"

PAIS = "US"  # Cambia esto: US, MX, CO, PE, AR, EC, etc.

response = requests.get(URL)
reader = csv.DictReader(io.StringIO(response.text))

aeropuertos = [row for row in reader if row['country'] == PAIS]

print(f"\nAeropuertos en {PAIS}: {len(aeropuertos)}\n")
for a in aeropuertos:
    print(f"{a['code']} | {a['name']} | {a['city']} | {a['country']}")