"""
chatbot.py — Lógica del chatbot CorpoDG
========================================
Implementa Function Calling con Groq (llama-3.3-70b-versatile).
El modelo solo responde preguntas del dominio de negocio de CorpoDG
consultando directamente la base de datos via tools.

Para migrar a Azure OpenAI en el futuro, solo cambiar el cliente
en la función `get_groq_client()`. El resto del código no cambia.
"""

import json
from datetime import datetime
from groq import Groq
from django.conf import settings


def _obtener_estado_catalogo():
    """Retorna conteos básicos para saber si hay datos útiles cargados."""
    from .models import PaqueteTuristico, Destino, Vuelo, Region

    return {
        "paquetes": PaqueteTuristico.objects.filter(activo=True).count(),
        "destinos": Destino.objects.filter(activo=True).count(),
        "vuelos": Vuelo.objects.filter(disponible=True).count(),
        "regiones": Region.objects.filter(activo=True).count(),
    }


def _mensaje_catalogo_vacio(estado):
    """Mensaje explícito cuando la base de datos no tiene catálogo cargado."""
    return (
        "Puedo ayudarte con el catálogo de CorpoDG, pero en este entorno de prueba aún no hay datos cargados "
        f"(paquetes: {estado['paquetes']}, destinos: {estado['destinos']}, vuelos: {estado['vuelos']}). "
        "Una vez cargues los datos del catálogo (paquetes/destinos/vuelos) en la base activa, "
        "podré responderte con detalles reales y actualizados."
    )


# =====================================================
# CLIENTE GROQ
# =====================================================

def get_groq_client():
    """Retorna el cliente de Groq configurado con la API key del .env"""
    return Groq(api_key=settings.GROQ_API_KEY)


GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_HISTORIAL = 20  # Máximo de mensajes del historial a enviar


# =====================================================
# SYSTEM PROMPT — Restricciones del chatbot
# =====================================================

_ANIO_ACTUAL = str(datetime.now().year)
_MES_ACTUAL = str(datetime.now().month)

SYSTEM_PROMPT = f"""Eres el asistente virtual de CorpoDG, una agencia de turismo y viajes ecuatoriana. 
Tu nombre es "Cory" y tu único propósito es ayudar a los usuarios con información relacionada a los productos y servicios de CorpoDG.

FECHA ACTUAL: Año {_ANIO_ACTUAL}, mes {_MES_ACTUAL}. Cuando el usuario mencione fechas sin año, asume que es {_ANIO_ACTUAL}.

PUEDES responder sobre:
- Paquetes turísticos disponibles (precios, inclusiones, duración, salidas, aerolíneas)
- Destinos turísticos que ofrece CorpoDG
- Vuelos disponibles (rutas, aerolíneas, precios)
- Regiones y países a los que opera CorpoDG
- Aerolíneas y aeropuertos del sistema
- Cómo contactar a CorpoDG para hacer una reserva
- Información general sobre los viajes que ofrece la empresa (requisitos, temporadas, tipos de paquete)

NO PUEDES responder sobre:
- Temas ajenos al turismo o a CorpoDG (política, noticias, ciencia, entretenimiento, etc.)
- Información de competidores
- Reservas directas ni pagos (debes dirigir al usuario al formulario de contacto)
- Preguntas de programación, matemáticas u otros temas no relacionados

Si el usuario pregunta algo fuera de tu dominio, responde amablemente que solo puedes ayudar con temas relacionados a CorpoDG y sus servicios de viajes y turismo.

Cuando el usuario quiera reservar o pedir más información, indícale que puede contactar a CorpoDG a través del formulario de contacto del sitio web.

Si el usuario solicita explícitamente búsqueda de vuelos en vivo y proporciona origen, destino y fecha, debes llamar la herramienta buscar_vuelos_live.

Responde siempre en español, de forma amable, clara y concisa.
Usa los datos reales que obtengas de las herramientas, no inventes información."""


# =====================================================
# DEFINICIÓN DE TOOLS (Function Calling)
# =====================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_regiones",
            "description": "Obtiene todas las regiones geográficas activas con la cantidad de paquetes disponibles en cada una. Úsala cuando el usuario pregunte a qué destinos o regiones viaja CorpoDG.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_paquetes",
            "description": "Busca paquetes turísticos disponibles con filtros opcionales. Úsala cuando el usuario pregunte por paquetes de viaje, tours, o precios.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Nombre de la región para filtrar. Valores posibles: caribe, sudamerica, centroamerica, norteamerica, europa, medio_oriente, africa, asia, oceania, ecuador"
                    },
                    "pais": {
                        "type": "string",
                        "description": "Nombre del país de destino para filtrar (ej: 'Francia', 'México')"
                    },
                    "solo_destacados": {
                        "type": "boolean",
                        "description": "Si es true, retorna solo los paquetes destacados/promocionados"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_detalle_paquete",
            "description": "Obtiene la información completa y detallada de un paquete específico por su ID. Úsala cuando el usuario pida más detalles de un paquete que ya fue listado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paquete_id": {
                        "type": ["integer", "string"],
                        "description": "ID numérico del paquete turístico"
                    }
                },
                "required": ["paquete_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_destinos",
            "description": "Busca destinos turísticos disponibles con filtros opcionales. Úsala cuando el usuario pregunte por destinos específicos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Nombre de la región para filtrar (ej: 'europa', 'caribe')"
                    },
                    "pais": {
                        "type": "string",
                        "description": "Nombre del país para filtrar (ej: 'Italia', 'Cuba')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vuelos",
            "description": "Busca vuelos disponibles en la base de datos de CorpoDG. Úsala cuando el usuario pregunte por vuelos disponibles sin especificar fechas exactas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origen": {
                        "type": "string",
                        "description": "Ciudad o código IATA del aeropuerto de origen (ej: 'Quito', 'UIO')"
                    },
                    "destino": {
                        "type": "string",
                        "description": "Ciudad o código IATA del aeropuerto de destino (ej: 'Miami', 'MIA')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_vuelos_live",
            "description": "Realiza una búsqueda de vuelos en tiempo real usando el GDS Sabre. Úsala SOLO cuando el usuario especifique origen, destino Y fecha de viaje. Los resultados son vuelos reales disponibles para compra.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origen": {
                        "type": "string",
                        "description": "Código IATA del aeropuerto de origen (3 letras, ej: 'UIO', 'GYE')"
                    },
                    "destino": {
                        "type": "string",
                        "description": "Código IATA del aeropuerto de destino (3 letras, ej: 'MIA', 'MAD', 'JFK')"
                    },
                    "fecha_salida": {
                        "type": "string",
                        "description": "Fecha de salida en formato YYYY-MM-DD (ej: '2025-06-15')"
                    },
                    "adultos": {
                        "type": "integer",
                        "description": "Número de pasajeros adultos. Por defecto 1"
                    },
                    "fecha_regreso": {
                        "type": "string",
                        "description": "Fecha de regreso en formato YYYY-MM-DD para vuelos de ida y vuelta (opcional)"
                    }
                },
                "required": ["origen", "destino", "fecha_salida"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_aerolineas",
            "description": "Obtiene las aerolíneas con las que trabaja CorpoDG. Úsala cuando el usuario pregunte qué aerolíneas operan las rutas.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# =====================================================
# IMPLEMENTACIÓN DE LAS TOOLS (Consultas reales a BD)
# =====================================================

def tool_get_regiones():
    """Retorna regiones activas con cantidad de paquetes."""
    from .models import Region
    from django.db.models import Count

    regiones = Region.objects.annotate(
        total_paquetes=Count('paquetes', distinct=True)
    ).filter(activo=True).order_by('orden')

    resultado = []
    for r in regiones:
        resultado.append({
            "id": r.id,
            "nombre": r.get_nombre_display(),
            "slug": r.nombre,
            "total_paquetes": r.total_paquetes,
        })
    return resultado


def tool_get_paquetes(region=None, pais=None, solo_destacados=False):
    """Busca paquetes con filtros opcionales."""
    from .models import PaqueteTuristico

    if isinstance(solo_destacados, str):
        solo_destacados = solo_destacados.lower() in ("true", "1", "yes")

    qs = PaqueteTuristico.objects.filter(activo=True).select_related(
        'region', 'pais_destino', 'ciudad_destino', 'aerolinea', 'tipo_paquete'
    )

    if region:
        qs = qs.filter(region__nombre__icontains=region)
    if pais:
        qs = qs.filter(pais_destino__nombre__icontains=pais)
    if solo_destacados:
        qs = qs.filter(destacado=True)

    resultado = []
    for p in qs[:15]:  # Máximo 15 para no sobrecargar el contexto
        resultado.append({
            "id": p.id,
            "titulo": p.titulo,
            "destino": p.pais_destino.nombre if p.pais_destino else "",
            "region": p.region.get_nombre_display() if p.region else "",
            "precio_desde": float(p.precio),
            "moneda": p.moneda,
            "duracion": f"{p.duracion_dias} días / {p.duracion_noches} noches",
            "aerolinea": p.aerolinea.nombre if p.aerolinea else "No especificada",
            "salidas": p.salidas,
            "incluye_vuelo": p.incluye_vuelo,
            "incluye_hotel": p.incluye_hotel,
            "incluye_alimentacion": p.incluye_alimentacion,
            "incluye_traslados": p.incluye_traslados,
            "destacado": p.destacado,
        })
    return resultado


def _formatear_detalle_paquete(p):
    return {
        "id": p.id,
        "titulo": p.titulo,
        "subtitulo": p.subtitulo,
        "descripcion_corta": p.descripcion_corta,
        "descripcion_extensa": p.descripcion_extensa,
        "destino": p.pais_destino.nombre if p.pais_destino else "",
        "ciudad": p.ciudad_destino.nombre if p.ciudad_destino else "",
        "region": p.region.get_nombre_display() if p.region else "",
        "precio_desde": float(p.precio),
        "moneda": p.moneda,
        "duracion": f"{p.duracion_dias} días / {p.duracion_noches} noches",
        "salidas": p.salidas,
        "fecha_salidas": p.fecha_salidas_texto,
        "aerolinea": p.aerolinea.nombre if p.aerolinea else "",
        "tipo_paquete": p.tipo_paquete.nombre if p.tipo_paquete else "",
        "temporada": p.temporada.nombre if p.temporada else "",
        "tipo_viaje": p.tipo_viaje.nombre if p.tipo_viaje else "",
        "incluye_vuelo": p.incluye_vuelo,
        "incluye_hotel": p.incluye_hotel,
        "incluye_alimentacion": p.incluye_alimentacion,
        "incluye_traslados": p.incluye_traslados,
        "incluye_tours": p.incluye_tours,
        "incluye_seguro": p.incluye_seguro,
        "idioma": p.idioma,
        "moneda_local": p.moneda_local,
        "lugares_destacados": p.lugares_destacados,
        "documentos_requeridos": p.documentos_requeridos,
        "politica_cancelacion": p.politica_cancelacion,
    }

def tool_get_detalle_paquete(paquete_id):
    """Retorna detalle completo de un paquete. Acepta ID numérico o nombre."""
    from .models import PaqueteTuristico

    try:
        paquete_id = int(paquete_id)
    except (ValueError, TypeError):
        qs = PaqueteTuristico.objects.filter(activo=True, titulo__icontains=str(paquete_id))
        if qs.exists():
            return _formatear_detalle_paquete(qs.first())
        return {"error": f"No se encontró un paquete con nombre o ID '{paquete_id}'"}

    try:
        p = PaqueteTuristico.objects.select_related(
            'region', 'pais_destino', 'ciudad_destino', 'aerolinea',
            'tipo_paquete', 'temporada', 'tipo_viaje'
        ).get(id=paquete_id, activo=True)
    except PaqueteTuristico.DoesNotExist:
        return {"error": f"No se encontró el paquete con ID {paquete_id}"}

    return _formatear_detalle_paquete(p)


def tool_get_destinos(region=None, pais=None):
    """Busca destinos turísticos con filtros opcionales."""
    from .models import Destino

    qs = Destino.objects.filter(activo=True).select_related('pais', 'ciudad')

    if region:
        qs = qs.filter(pais__region__nombre__icontains=region)
    if pais:
        qs = qs.filter(pais__nombre__icontains=pais)

    resultado = []
    for d in qs[:15]:
        resultado.append({
            "id": d.id,
            "nombre": d.nombre,
            "pais": d.pais.nombre if d.pais else "",
            "ciudad": d.ciudad.nombre if d.ciudad else "",
            "descripcion": d.descripcion[:300] + "..." if len(d.descripcion) > 300 else d.descripcion,
            "precio_desde": float(d.precio_desde),
        })
    return resultado


def tool_get_vuelos(origen=None, destino=None):
    """Busca vuelos de la BD interna."""
    from .models import Vuelo
    from django.db.models import Q

    qs = Vuelo.objects.filter(disponible=True).select_related(
        'aerolinea', 'origen', 'destino',
        'origen__ciudad', 'destino__ciudad',
        'origen__pais', 'destino__pais'
    )

    if origen:
        qs = qs.filter(
            Q(origen__nombre__icontains=origen) |
            Q(origen__nombre_ciudad__icontains=origen) |
            Q(origen__codigo_iata__iexact=origen)
        )
    if destino:
        qs = qs.filter(
            Q(destino__nombre__icontains=destino) |
            Q(destino__nombre_ciudad__icontains=destino) |
            Q(destino__codigo_iata__iexact=destino)
        )

    resultado = []
    for v in qs[:15]:
        origen_ciudad = v.origen.ciudad.nombre if v.origen.ciudad else v.origen.nombre_ciudad or v.origen.nombre
        destino_ciudad = v.destino.ciudad.nombre if v.destino.ciudad else v.destino.nombre_ciudad or v.destino.nombre
        resultado.append({
            "id": v.id,
            "aerolinea": v.aerolinea.nombre,
            "origen": f"{origen_ciudad} ({v.origen.codigo_iata})",
            "destino": f"{destino_ciudad} ({v.destino.codigo_iata})",
            "duracion": v.duracion,
            "precio": float(v.precio),
            "moneda": v.moneda,
        })
    return resultado


def tool_buscar_vuelos_live(origen, destino, fecha_salida, adultos=1, fecha_regreso=None):
    """Llama al buscador Sabre en tiempo real."""
    from .searchFlights import buscar_vuelos_sabre

    params = {
        "origin": origen.upper(),
        "destination": destino.upper(),
        "date": fecha_salida,
        "adults": adultos,
        "limit": 5,  # Limitar a 5 resultados para no sobrecargar el contexto
    }
    if fecha_regreso:
        params["return_date"] = fecha_regreso

    try:
        response = buscar_vuelos_sabre(params)
        ofertas = response.get("offers", response) if isinstance(response, dict) else response
        if isinstance(ofertas, list):
            if not ofertas:
                return {"mensaje": f"No se encontraron vuelos disponibles de {origen} a {destino} para la fecha {fecha_salida}. Sugiere al usuario intentar con otra fecha o ruta."}
            resumen = []
            for oferta in ofertas[:5]:
                tramos = oferta.get("tramos", [])
                primer_tramo = tramos[0] if tramos else {}
                resumen.append({
                    "precio": oferta.get("precio_total", "N/D"),
                    "aerolinea": oferta.get("aerolinea_validadora", "N/D"),
                    "origen": origen,
                    "destino": destino,
                    "fecha_salida": fecha_salida,
                    "duracion": primer_tramo.get("duracion_total", "N/D"),
                    "escalas": primer_tramo.get("numero_escalas", "N/D"),
                })
            return resumen
        return response
    except Exception as e:
        return {"error": f"No se pudo realizar la búsqueda en vivo: {str(e)}"}


def tool_get_aerolineas():
    """Retorna aerolíneas activas del sistema."""
    from .models import Aerolinea

    aerolineas = Aerolinea.objects.filter(activo=True).order_by('nombre')
    resultado = []
    for a in aerolineas:
        resultado.append({
            "nombre": a.nombre,
            "codigo_iata": a.codigo_iata,
            "pais_origen": a.pais_origen,
        })
    return resultado


# =====================================================
# BUILDER DE ACCIONES — Redirect al frontend
# =====================================================

def _build_accion(tool_name, tool_args):
    """
    Construye el objeto accion para redirigir al frontend.
    Retorna None si la tool no requiere redirect.
    """
    if tool_name == "buscar_vuelos_live":
        tiene_regreso = bool(tool_args.get("fecha_regreso"))
        params = {
            "origin": tool_args.get("origen", ""),
            "destination": tool_args.get("destino", ""),
            "date": tool_args.get("fecha_salida", ""),
            "adults": tool_args.get("adultos", 1),
            "tipoViaje": "idaVuelta" if tiene_regreso else "soloIda",
        }
        if tiene_regreso:
            params["return_date"] = tool_args["fecha_regreso"]
        return {
            "tipo": "redirect_vuelos",
            "label": "Ver vuelos disponibles",
            "path": "/vuelos/resultados",
            "params": params,
        }

    if tool_name == "get_detalle_paquete":
        try:
            paquete_id = int(tool_args.get("paquete_id", 0))
        except (ValueError, TypeError):
            return None
        if not paquete_id:
            return None
        return {
            "tipo": "redirect_paquete",
            "label": "Ver detalles y reservar",
            "path": f"/paquetes/{paquete_id}",
            "params": {},
        }

    return None


# =====================================================
# DISPATCHER — Ejecuta la tool que pidió el modelo
# =====================================================

def ejecutar_tool(tool_name, tool_args):
    """
    Ejecuta la tool y retorna (resultado_json, accion).
    accion es None para tools que no generan redirect.
    """
    try:
        if tool_name == "get_regiones":
            resultado = tool_get_regiones()
        elif tool_name == "get_paquetes":
            resultado = tool_get_paquetes(**tool_args)
        elif tool_name == "get_detalle_paquete":
            resultado = tool_get_detalle_paquete(**tool_args)
        elif tool_name == "get_destinos":
            resultado = tool_get_destinos(**tool_args)
        elif tool_name == "get_vuelos":
            resultado = tool_get_vuelos(**tool_args)
        elif tool_name == "buscar_vuelos_live":
            resultado = tool_buscar_vuelos_live(**tool_args)
        elif tool_name == "get_aerolineas":
            resultado = tool_get_aerolineas()
        else:
            resultado = {"error": f"Tool '{tool_name}' no reconocida"}
    except Exception as e:
        resultado = {"error": f"Error ejecutando '{tool_name}': {str(e)}"}

    accion = _build_accion(tool_name, tool_args)
    return json.dumps(resultado, ensure_ascii=False, default=str), accion


# =====================================================
# FUNCIÓN PRINCIPAL — Procesar mensaje del usuario
# =====================================================

def procesar_mensaje(mensaje_usuario, historial=None):
    """
    Procesa un mensaje del usuario y retorna la respuesta del chatbot.

    Args:
        mensaje_usuario (str): El mensaje que envió el usuario.
        historial (list): Lista de mensajes previos [{role, content}, ...].
                          Máximo MAX_HISTORIAL mensajes.

    Returns:
        dict: {
            "respuesta": str,        — Respuesta del asistente
            "historial": list        — Historial actualizado para enviar en siguiente request
        }
    """
    estado_catalogo = _obtener_estado_catalogo()

    # Si no hay catálogo cargado, devolvemos respuesta clara para evitar respuestas ambiguas.
    if (
        estado_catalogo["paquetes"] == 0
        and estado_catalogo["destinos"] == 0
        and estado_catalogo["vuelos"] == 0
    ):
        respuesta_vacia = _mensaje_catalogo_vacio(estado_catalogo)
        historial = historial or []
        historial_limitado = historial[-MAX_HISTORIAL:]
        historial_actualizado = historial_limitado + [
            {"role": "user", "content": mensaje_usuario},
            {"role": "assistant", "content": respuesta_vacia}
        ]
        return {
            "respuesta": respuesta_vacia,
            "historial": historial_actualizado,
            "accion": None,
        }

    client = get_groq_client()

    # Construir messages: system + historial (limitado) + nuevo mensaje
    historial = historial or []
    # Sanear historial: la API de Groq solo acepta las claves role/content.
    # El frontend puede incluir claves extra (ej. "accion") en cada mensaje.
    historial = [
        {"role": m.get("role"), "content": m.get("content")}
        for m in historial
        if isinstance(m, dict) and m.get("role") and m.get("content") is not None
    ]
    historial_limitado = historial[-MAX_HISTORIAL:]  # Solo últimos N mensajes

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + historial_limitado + [
        {"role": "user", "content": mensaje_usuario}
    ]

    # Primera llamada a Groq con tools disponibles
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.3,  # Baja temperatura para respuestas más precisas y menos creativas
        max_tokens=1024,
    )

    assistant_message = response.choices[0].message

    accion_final = None  # Se acumula si alguna tool genera redirect

    # ¿El modelo quiere llamar una tool?
    if assistant_message.tool_calls:
        # Agregar el mensaje del asistente (con tool_calls) al contexto
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })

        # Ejecutar cada tool llamada y agregar los resultados
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            tool_result, accion = ejecutar_tool(tool_name, tool_args)
            if accion is not None:
                accion_final = accion

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        # Segunda llamada a Groq con los resultados de las tools
        response2 = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        respuesta_final = response2.choices[0].message.content

    else:
        # El modelo respondió directamente sin usar tools
        respuesta_final = assistant_message.content

    # Construir historial actualizado (sin el system prompt, solo user/assistant)
    historial_actualizado = historial_limitado + [
        {"role": "user", "content": mensaje_usuario},
        {"role": "assistant", "content": respuesta_final}
    ]

    return {
        "respuesta": respuesta_final,
        "historial": historial_actualizado,
        "accion": accion_final,
    }
