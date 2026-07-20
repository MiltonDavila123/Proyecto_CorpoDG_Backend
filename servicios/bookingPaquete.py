"""Reserva de PAQUETES turísticos: Stripe Checkout + voucher por correo.

Espejo del flujo de vuelos (``bookingFlight.py``) pero para paquetes:

  1) POST /paquetes/booking/checkout/  -> crea Stripe Checkout Session.
                                          Guarda en cache el "intent"
                                          (paquete, viajeros, contacto,
                                          n_personas) con la session_id.
  2) Usuario paga en Stripe (test mode 4242 4242 4242 4242).
  3) POST /paquetes/booking/confirm/   -> { session_id }
                                          Verifica el pago, genera la
                                          reserva normalizada del paquete
                                          (localizador, totales) y la
                                          devuelve.
  4) Se envía el voucher por correo (PDF adjunto) de forma asíncrona.

Modo SANDBOX (BOOKING_SANDBOX=1, default): no llama a ningún proveedor
externo, sólo confirma el pago Stripe y arma la reserva.
"""

import datetime as _dt
import json
import random
import string

try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None

try:
    from django.core.cache import cache as _cache
except ImportError:  # pragma: no cover
    _cache = None

# Reutilizamos los helpers ya probados del flujo de vuelos.
from .bookingFlight import (
    _setting,
    _set_stripe_key,
    _booking_sandbox_activo,
    _enviar_correo_activo,
    _stripe_receipt_url,
    _ahora_ecuador,
)


# Cache keys / TTL
_INTENT_KEY = "paquete_intent:{sid}"
_RESULT_KEY = "paquete_result:{sid}"
_RESULT_LOC_KEY = "paquete_result_loc:{loc}"
_INTENT_TTL = 60 * 60 * 24          # 24 h
_RESULT_TTL = 60 * 60 * 24 * 7      # 7 días


def _localizador(longitud=6):
    return "CDGPK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=longitud))


# ---------------------------------------------------------------------------
# Carga del paquete desde la BD (snapshot para la reserva)
# ---------------------------------------------------------------------------

def _snapshot_paquete(paquete_id):
    """Devuelve un dict con los datos del paquete o None si no existe."""
    try:
        from .models import PaqueteTuristico
    except Exception:  # pragma: no cover
        return None
    paq = (PaqueteTuristico.objects
           .filter(id=paquete_id, activo=True)
           .select_related("region", "pais_destino", "ciudad_destino", "aerolinea")
           .first())
    if not paq:
        return None

    destino = paq.pais_destino.nombre if paq.pais_destino else ""
    ciudad = paq.ciudad_destino.nombre if paq.ciudad_destino else ""
    destino_completo = f"{ciudad}, {destino}" if ciudad else destino

    aero = None
    if paq.aerolinea:
        aero = {
            "codigo": getattr(paq.aerolinea, "codigo_iata", None),
            "nombre": getattr(paq.aerolinea, "nombre", None),
            "logo": (getattr(paq.aerolinea, "logo_url", None)
                     or getattr(paq.aerolinea, "brandmark_url", None)),
        }

    lugares = []
    if paq.lugares_destacados:
        lugares = [x.strip() for x in paq.lugares_destacados.split(",") if x.strip()]

    return {
        "id": paq.id,
        "titulo": paq.titulo,
        "subtitulo": paq.subtitulo,
        "destino": destino_completo,
        "pais": destino,
        "ciudad": ciudad,
        "imagen_url": paq.imagen_url,
        "descripcion_corta": paq.descripcion_corta,
        "duracion_noches": paq.duracion_noches,
        "duracion_dias": paq.duracion_dias,
        "salidas": paq.salidas,
        "fecha_salidas_texto": paq.fecha_salidas_texto,
        "precio": float(paq.precio),
        "moneda": paq.moneda or "USD",
        "temperatura": paq.temperatura,
        "idioma": paq.idioma,
        "moneda_local": paq.moneda_local,
        "documentos_requeridos": paq.documentos_requeridos,
        "lugares_destacados": lugares,
        "incluye": {
            "vuelo": paq.incluye_vuelo,
            "hotel": paq.incluye_hotel,
            "alimentacion": paq.incluye_alimentacion,
            "traslados": paq.incluye_traslados,
            "tours": paq.incluye_tours,
            "seguro": paq.incluye_seguro,
        },
        "aerolinea": aero,
        "pdf_url": paq.pdf_url,
    }


# ---------------------------------------------------------------------------
# Stripe Checkout
# ---------------------------------------------------------------------------

def crear_checkout_paquete(datos):
    """
    datos = {
      "paquete_id": 12,                       # obligatorio
      "n_personas": 2,                        # obligatorio (>=1)
      "contacto": {"email": "...", "phone": "..."},   # email obligatorio
      "viajeros": [                            # opcional (nombres)
        {"nombre": "Milton", "apellido": "Davila", "documento": "..."},
        ...
      ],
      "fecha_viaje": "2026-08-15",            # opcional
      "moneda": "USD",                        # opcional (default: la del paquete)
      "success_url": "...",                   # opcional
      "cancel_url":  "..."
    }
    """
    paquete_id = datos.get("paquete_id")
    n_personas = int(datos.get("n_personas") or 0)
    contacto = datos.get("contacto") or {}
    viajeros = datos.get("viajeros") or []
    fecha_viaje = datos.get("fecha_viaje")

    if not paquete_id:
        return {"error": "Falta 'paquete_id'", "code": 400}
    if n_personas < 1:
        return {"error": "'n_personas' debe ser >= 1", "code": 400}
    if not contacto.get("email"):
        return {"error": "Falta 'contacto.email'", "code": 400}

    paquete = _snapshot_paquete(paquete_id)
    if not paquete:
        return {"error": "Paquete no encontrado o inactivo", "code": 404}

    moneda = (datos.get("moneda") or paquete["moneda"] or "USD").lower()
    precio_unitario = float(paquete["precio"])
    total = round(precio_unitario * n_personas, 2)
    if total <= 0:
        return {"error": "Monto total inválido (0)", "code": 400}
    monto_centavos = int(round(total * 100))

    success_url = (datos.get("success_url")
                   or _setting("FRONTEND_PAQUETE_SUCCESS_URL", None)
                   or _setting("FRONTEND_BOOKING_SUCCESS_URL",
                               "http://localhost:5173/reserva/confirmada"))
    cancel_url = (datos.get("cancel_url")
                  or _setting("FRONTEND_PAQUETE_CANCEL_URL", None)
                  or _setting("FRONTEND_BOOKING_CANCEL_URL",
                              "http://localhost:5173/reserva/cancelada"))
    if "{CHECKOUT_SESSION_ID}" not in success_url:
        sep = "&" if "?" in success_url else "?"
        success_url = f"{success_url}{sep}session_id={{CHECKOUT_SESSION_ID}}"

    try:
        _set_stripe_key()
    except RuntimeError as e:
        return {"error": str(e), "code": 500}

    descripcion = (
        f"{paquete['titulo']} - {paquete['destino']} "
        f"({paquete['duracion_dias']}d/{paquete['duracion_noches']}n) - "
        f"{n_personas} persona(s)"
    )

    line_items = [{
        "price_data": {
            "currency": moneda,
            "product_data": {
                "name": f"Paquete CorpoDG - {paquete['titulo']}",
                "description": descripcion[:255],
            },
            "unit_amount": monto_centavos,
        },
        "quantity": 1,
    }]

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=contacto.get("email"),
            metadata={
                "tipo": "paquete",
                "paquete_id": str(paquete_id),
                "destino": paquete["destino"][:80],
                "personas": str(n_personas),
            },
        )
    except Exception as e:  # noqa: BLE001
        return {"error": f"Stripe rechazó la sesión: {e}", "code": 502}

    intent = {
        "tipo": "paquete",
        "stripe_session_id": session.id,
        "paquete": paquete,
        "n_personas": n_personas,
        "viajeros": viajeros,
        "contacto": contacto,
        "fecha_viaje": fecha_viaje,
        "moneda": moneda.upper(),
        "precio_unitario": precio_unitario,
        "total": total,
        "creado": _dt.datetime.utcnow().isoformat() + "Z",
    }
    if _cache is not None:
        _cache.set(_INTENT_KEY.format(sid=session.id),
                   json.dumps(intent), _INTENT_TTL)

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "paquete_id": paquete_id,
        "monto": total,
        "moneda": moneda.upper(),
        "n_personas": n_personas,
        "expira": (_dt.datetime.utcnow() + _dt.timedelta(hours=24))
                    .isoformat() + "Z",
    }


def _recuperar_intent(session_id):
    if _cache is None:
        return None
    raw = _cache.get(_INTENT_KEY.format(sid=session_id))
    if not raw:
        return None
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Confirmación (post-pago)
# ---------------------------------------------------------------------------

def confirmar_reserva_paquete(session_id):
    if not session_id:
        return {"error": "Falta 'session_id'", "code": 400}

    try:
        _set_stripe_key()
        session = stripe.checkout.Session.retrieve(session_id)
    except RuntimeError as e:
        return {"error": str(e), "code": 500}
    except Exception as e:  # noqa: BLE001
        return {"error": f"No se pudo verificar la sesión Stripe: {e}", "code": 502}

    pago_ok = (session.payment_status == "paid"
               or session.payment_status == "no_payment_required")
    if not pago_ok:
        return {
            "error": "El pago aún no está completado",
            "code": 402,
            "payment_status": session.payment_status,
        }

    intent = _recuperar_intent(session_id)
    if not intent:
        return {
            "error": "No se encontró el intento de reserva (puede haber expirado)",
            "code": 404,
        }

    reserva = _armar_reserva_paquete(intent)
    reserva["sandbox"] = _booking_sandbox_activo()

    # Datos de pago Stripe
    reserva["pago"] = {
        "proveedor": "stripe",
        "estado": session.payment_status,
        "monto": (session.amount_total or 0) / 100.0,
        "moneda": (session.currency or "usd").upper(),
        "stripe_session_id": session.id,
        "stripe_payment_intent": session.payment_intent,
        "recibo_url": _stripe_receipt_url(session),
        "email": session.customer_details.email if session.customer_details else None,
    }

    reserva["correo"] = {"enviado": False, "estado": "en_proceso",
                         "mensaje": "El voucher se está enviando por correo."}
    _guardar_reserva(session_id, reserva)

    # Persistir la reserva en la base de datos (gestión desde el admin)
    _guardar_reserva_bd(session_id, reserva, intent)

    _enviar_voucher_email_async(session_id, reserva, intent)

    return reserva


def _guardar_reserva_bd(session_id, reserva, intent):
    """Persiste la reserva del paquete en la BD para gestión desde el admin.

    Idempotente por stripe_session_id. Nunca rompe el flujo de confirmación:
    los errores solo se loguean.
    """
    import logging
    try:
        from .models import Cliente, PaqueteTuristico, ReservaPaquete

        paquete_info = intent.get("paquete") or {}
        contacto = intent.get("contacto") or {}
        pago = reserva.get("pago") or {}
        totales = reserva.get("totales") or {}
        email = contacto.get("email") or pago.get("email") or ""
        telefono = contacto.get("phone") or ""

        paquete_obj = PaqueteTuristico.objects.filter(
            id=paquete_info.get("id")
        ).first()

        obj, creada = ReservaPaquete.objects.get_or_create(
            stripe_session_id=session_id,
            defaults={
                "localizador": reserva.get("localizador") or "",
                "paquete": paquete_obj,
                "paquete_titulo": paquete_info.get("titulo") or "",
                "email": email,
                "telefono": telefono,
                "n_personas": int(intent.get("n_personas") or 1),
                "fecha_viaje": intent.get("fecha_viaje") or "",
                "viajeros": reserva.get("viajeros") or [],
                "monto": totales.get("total") or pago.get("monto") or 0,
                "moneda": totales.get("moneda") or pago.get("moneda") or "USD",
                "sandbox": bool(reserva.get("sandbox")),
                "datos": reserva,
            },
        )

        # Avisar al correo configurado en el admin (solo la primera vez)
        if creada:
            from .notifications import notificar_nueva_reserva_async
            notificar_nueva_reserva_async(
                tipo="paquete",
                codigo=obj.localizador,
                email_cliente=email,
                telefono_cliente=telefono,
                monto=obj.monto,
                moneda=obj.moneda,
                detalle=obj.paquete_titulo,
                detalle_extra={"Personas": obj.n_personas,
                               "Fecha de viaje": obj.fecha_viaje or "No indicada"},
            )

        # Registrar/actualizar también al cliente para su gestión
        if email:
            viajeros = reserva.get("viajeros") or [{}]
            nombre = (viajeros[0].get("nombre") or "").strip() or email.split("@")[0]
            Cliente.objects.get_or_create(
                email=email,
                defaults={"nombre_completo": nombre[:50],
                          "telefono": telefono[:15]},
            )
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).exception(
            "No se pudo persistir la reserva de paquete %s en la BD", session_id
        )


def _armar_reserva_paquete(intent):
    """Construye la reserva normalizada del paquete a partir del intent."""
    paquete = intent["paquete"]
    n = int(intent["n_personas"])
    precio_unitario = float(intent["precio_unitario"])
    total = round(precio_unitario * n, 2)
    moneda = intent.get("moneda") or paquete.get("moneda") or "USD"

    viajeros = []
    for v in (intent.get("viajeros") or []):
        nombre = " ".join(
            x for x in [(v.get("nombre") or "").strip(),
                        (v.get("apellido") or "").strip()] if x
        ).strip()
        if nombre:
            viajeros.append({"nombre": nombre, "documento": v.get("documento")})
    if not viajeros:
        # Si no enviaron nombres, dejamos al menos el contacto como titular.
        email = (intent.get("contacto") or {}).get("email") or ""
        viajeros = [{"nombre": email.split("@")[0].upper() or "TITULAR",
                     "documento": None}]

    now = _ahora_ecuador()
    return {
        "tipo": "paquete",
        "localizador": _localizador(),
        "estado": "CONFIRMADA",
        "emitida": True,
        "fecha_creacion": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "paquete": paquete,
        "viajeros": viajeros,
        "n_personas": n,
        "fecha_viaje": intent.get("fecha_viaje"),
        "contacto": intent.get("contacto") or {},
        "precio_unitario": precio_unitario,
        "moneda": moneda,
        "totales": {
            "precio_unitario": precio_unitario,
            "n_personas": n,
            "subtotal": total,
            "total": total,
            "moneda": moneda,
        },
    }


# ---------------------------------------------------------------------------
# Cache de resultados
# ---------------------------------------------------------------------------

def _guardar_reserva(session_id, reserva):
    if _cache is None:
        return
    try:
        loc = reserva.get("localizador")
        payload = json.dumps(reserva)
        if session_id:
            _cache.set(_RESULT_KEY.format(sid=session_id), payload, _RESULT_TTL)
        if loc:
            _cache.set(_RESULT_LOC_KEY.format(loc=loc), payload, _RESULT_TTL)
    except Exception:  # noqa: BLE001
        pass


def obtener_reserva_paquete_guardada(clave):
    """Recupera una reserva de paquete por session_id o por localizador."""
    if _cache is None or not clave:
        return None
    raw = (_cache.get(_RESULT_KEY.format(sid=clave))
           or _cache.get(_RESULT_LOC_KEY.format(loc=clave)))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Correo (asíncrono)
# ---------------------------------------------------------------------------

def _enviar_voucher_email(reserva, intent):
    """Envía el voucher del paquete por correo (best-effort)."""
    if not _enviar_correo_activo():
        return
    try:
        from .paqueteDocs import enviar_correo_paquete
        from .notifications import obtener_destinatarios_notificacion
        # Copia a los correos de administración configurados en el admin
        destinatarios = obtener_destinatarios_notificacion()
        contacto_email = (intent.get("contacto") or {}).get("email")
        if contacto_email and contacto_email not in destinatarios:
            destinatarios.insert(0, contacto_email)
        res = enviar_correo_paquete(reserva, destinatarios=destinatarios)
        reserva["correo"] = {
            "enviado": bool(res.get("success")),
            "mensaje": res.get("message"),
            "destinatarios": res.get("destinatarios"),
        }
    except Exception as e:  # noqa: BLE001
        reserva["correo"] = {"enviado": False, "mensaje": str(e)}


def _enviar_voucher_email_async(session_id, reserva, intent):
    """Genera el PDF + envía el correo en un hilo de fondo."""
    if not _enviar_correo_activo():
        return

    def _worker():
        try:
            _enviar_voucher_email(reserva, intent)
        except Exception:  # noqa: BLE001
            pass
        try:
            _guardar_reserva(session_id, reserva)
        except Exception:  # noqa: BLE001
            pass

    import threading
    threading.Thread(target=_worker, daemon=True).start()
