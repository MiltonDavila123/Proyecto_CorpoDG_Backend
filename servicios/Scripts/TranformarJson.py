import json

with open("servicios/Scripts/paises_por_region copy.json", "r", encoding="utf-8") as f:
    data = json.load(f)

nuevo = {
    "caribe": [],
    "sudamerica": [],
    "centroamerica": [],
    "norteamerica": [],
    "europa": data.get("europe", []),
    "medio_oriente": [],
    "africa": data.get("africa", []),
    "asia": [],
    "oceania": data.get("oceania",[]),
    "ecuador": []
}

# =====================
# DIVIDIR AMÉRICAS
# =====================

for pais in data["americas"]:
    nombre = pais["nombre_es"]

    if nombre == "Ecuador":
        nuevo["ecuador"].append(pais)

    elif nombre in ["Argentina","Bolivia","Brasil","Chile","Colombia","Paraguay","Perú","Uruguay","Venezuela","Guyana","Surinam"]:
        nuevo["sudamerica"].append(pais)

    elif nombre in ["Guatemala","Belice","El Salvador","Honduras","Nicaragua","Costa Rica","Panamá"]:
        nuevo["centroamerica"].append(pais)

    elif nombre in ["Canadá","Estados Unidos","México","Groenlandia"]:
        nuevo["norteamerica"].append(pais)

    else:
        nuevo["caribe"].append(pais)

# =====================
# SEPARAR MEDIO ORIENTE DE ASIA
# =====================

medio_oriente_lista = [
    "Arabia Saudí",
    "Emiratos Árabes Unidos",
    "Qatar",
    "Kuwait",
    "Omán",
    "Yemen",
    "Irak",
    "Iran",
    "Israel",
    "Jordania",
    "Líbano",
    "Siria",
    "Turquía",
    "Palestina",
    "Bahrein"
]

for pais in data["asia"]:
    nombre = pais["nombre_es"]

    if nombre in medio_oriente_lista:
        nuevo["medio_oriente"].append(pais)
    else:
        nuevo["asia"].append(pais)


with open("nuevo_paises.json", "w", encoding="utf-8") as f:
    json.dump(nuevo, f, ensure_ascii=False, indent=2)