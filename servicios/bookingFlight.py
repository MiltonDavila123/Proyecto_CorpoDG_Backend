"""Booking flow: Stripe Checkout + simulador Sabre createBooking.

Flujo:
  1) POST /booking/checkout/   -> crea Stripe Checkout Session.
                                  Guarda en cache el "intent" (opcion, pax,
                                  asientos, contacto) con la session_id de
                                  Stripe como key.
  2) Usuario paga en Stripe (test mode con tarjetas 4242 4242 4242 4242).
  3) POST /booking/confirm/    -> { session_id }
                                  Verifica que el pago haya sido exitoso,
                                  llama (o simula) Sabre /createBooking,
                                  devuelve la reserva normalizada
                                  (PNR, ticket, breakdown).
  4) (Opcional) Stripe webhook -> /booking/webhook/

Modo SANDBOX:
  Si BOOKING_SANDBOX=1 (default) no llama a Sabre, genera respuesta
  simulada con la estructura de createBookingResponse.
"""

import datetime as _dt
import json
import os
import random
import string
import uuid

try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None

try:
    from django.conf import settings as _django_settings
    from django.core.cache import cache as _cache
except ImportError:  # pragma: no cover
    _django_settings = None
    _cache = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setting(name, default=None):
    if _django_settings is not None:
        val = getattr(_django_settings, name, None)
        if val is not None:
            return val
    return os.getenv(name, default)


def _booking_sandbox_activo():
    val = _setting("BOOKING_SANDBOX", "1")
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def _stripe_key():
    return _setting("STRIPE_SECRET_KEY", "")


def _set_stripe_key():
    if stripe is None:
        raise RuntimeError("La libreria 'stripe' no esta instalada (pip install stripe)")
    key = _stripe_key()
    if not key or "REEMPLAZAR" in key:
        raise RuntimeError(
            "STRIPE_SECRET_KEY no configurada. Setea tu sk_test_... en .env"
        )
    stripe.api_key = key


def _pnr_random(longitud=6):
    return "".join(random.choices(string.ascii_uppercase, k=longitud))


def _ticket_number(prefix="001"):
    return f"{prefix}{random.randint(1000000000, 9999999999)}"


def _booking_id():
    return f"1S{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"


# ---------------------------------------------------------------------------
# Stripe Checkout
# ---------------------------------------------------------------------------

def crear_checkout(datos):
    """
    datos = {
      "opcion": {...},                       # opcion del buscador
      "pasajeros": [ {givenName, surname, email, phone, ...}, ... ],
      "contacto": {"email": "...", "phone": "..."},
      "asientos_seleccionados": [            # opcional
        {"segmento_indice": 1, "pasajero_id": 0,
         "asiento_id": "17F", "offer_item_id": "OITEM-...", "monto": 8.0}
      ],
      "moneda": "USD",
      "success_url": "...",                  # opcional, override del default
      "cancel_url":  "..."
    }
    """
    opcion = datos.get("opcion") or {}
    pasajeros = datos.get("pasajeros") or []
    contacto = datos.get("contacto") or {}
    asientos = datos.get("asientos_seleccionados") or []
    moneda = (datos.get("moneda") or opcion.get("moneda") or "USD").lower()

    if not opcion.get("tramos"):
        return {"error": "Falta 'opcion' con sus 'tramos'", "code": 400}
    if not pasajeros:
        return {"error": "Falta lista de 'pasajeros'", "code": 400}
    if not contacto.get("email"):
        return {"error": "Falta 'contacto.email'", "code": 400}

    # Monto total
    precio_vuelo = float(opcion.get("precio_total") or 0)
    extra_asientos = sum(float(a.get("monto") or 0) for a in asientos)
    n_pax = len(pasajeros)
    total = round(precio_vuelo + extra_asientos, 2)

    if total <= 0:
        return {"error": "Monto total invalido (0)", "code": 400}

    # Stripe usa centavos
    monto_centavos = int(round(total * 100))

    # Descripcion legible
    primer_tramo = opcion["tramos"][0]
    ultimo_tramo = opcion["tramos"][-1]
    origen = primer_tramo.get("origen", {}).get("aeropuerto", "")
    destino = primer_tramo.get("destino", {}).get("aeropuerto", "")
    if len(opcion["tramos"]) > 1:
        destino_final = ultimo_tramo.get("destino", {}).get("aeropuerto", "")
        ruta = f"{origen} <-> {destino} ({destino_final})"
    else:
        ruta = f"{origen} -> {destino}"

    descripcion = (
        f"Vuelo {ruta} - {n_pax} pax"
        + (f" + {len(asientos)} asientos" if asientos else "")
    )

    success_url = (datos.get("success_url")
                   or _setting("FRONTEND_BOOKING_SUCCESS_URL",
                               "http://localhost:5173/reserva/confirmada"))
    cancel_url = (datos.get("cancel_url")
                  or _setting("FRONTEND_BOOKING_CANCEL_URL",
                              "http://localhost:5173/reserva/cancelada"))

    # Stripe redirige con ?session_id={CHECKOUT_SESSION_ID}
    if "{CHECKOUT_SESSION_ID}" not in success_url:
        sep = "&" if "?" in success_url else "?"
        success_url = f"{success_url}{sep}session_id={{CHECKOUT_SESSION_ID}}"

    try:
        _set_stripe_key()
    except RuntimeError as e:
        return {"error": str(e), "code": 500}

    booking_ref = uuid.uuid4().hex[:12].upper()

    line_items = [{
        "price_data": {
            "currency": moneda,
            "product_data": {
                "name": f"Reserva CorpoDG - {ruta}",
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
                "booking_ref": booking_ref,
                "ruta": ruta,
                "pax": str(n_pax),
                "asientos": str(len(asientos)),
            },
        )
    except Exception as e:  # noqa: BLE001
        return {"error": f"Stripe rechazo la sesion: {e}", "code": 502}

    # Guardar intento en cache (24h) para poder confirmar luego
    intent = {
        "booking_ref": booking_ref,
        "stripe_session_id": session.id,
        "opcion": opcion,
        "pasajeros": pasajeros,
        "contacto": contacto,
        "asientos_seleccionados": asientos,
        "moneda": moneda.upper(),
        "total": total,
        "creado": _dt.datetime.utcnow().isoformat() + "Z",
    }
    if _cache is not None:
        _cache.set(f"booking_intent:{session.id}", json.dumps(intent), 60 * 60 * 24)

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "booking_ref": booking_ref,
        "monto": total,
        "moneda": moneda.upper(),
        "expira": (_dt.datetime.utcnow() + _dt.timedelta(hours=24))
                    .isoformat() + "Z",
    }


def _recuperar_intent(session_id):
    if _cache is None:
        return None
    raw = _cache.get(f"booking_intent:{session_id}")
    if not raw:
        return None
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Confirm booking (post-pago)
# ---------------------------------------------------------------------------

def confirmar_reserva(session_id):
    if not session_id:
        return {"error": "Falta 'session_id'", "code": 400}

    try:
        _set_stripe_key()
        session = stripe.checkout.Session.retrieve(session_id)
    except RuntimeError as e:
        return {"error": str(e), "code": 500}
    except Exception as e:  # noqa: BLE001
        return {"error": f"No se pudo verificar la sesion Stripe: {e}", "code": 502}

    pago_ok = (session.payment_status == "paid"
               or session.payment_status == "no_payment_required")
    if not pago_ok:
        return {
            "error": "El pago aun no esta completado",
            "code": 402,
            "payment_status": session.payment_status,
        }

    intent = _recuperar_intent(session_id)
    if not intent:
        return {
            "error": "No se encontro el intento de reserva (puede haber expirado)",
            "code": 404,
        }

    # Llamar Sabre createBooking (real) o simular
    if _booking_sandbox_activo():
        reserva = _simular_create_booking(intent, session)
        reserva["sandbox"] = True
    else:
        reserva = _llamar_sabre_create_booking(intent)

    if "error" in reserva:
        return reserva

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

    # Cachear la reserva final (para la vista imprimible / PDF posterior)
    reserva["correo"] = {"enviado": False, "estado": "en_proceso",
                         "mensaje": "El voucher se está enviando por correo."}
    _guardar_reserva(session_id, reserva)

    # Enviar voucher por correo de forma ASÍNCRONA (no bloquea la respuesta):
    # generar 2 PDFs + SMTP puede tardar varios segundos.
    _enviar_voucher_email_async(session_id, reserva, intent)

    return reserva


def _enviar_correo_activo():
    val = _setting("BOOKING_SEND_EMAIL", "1")
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def _guardar_reserva(session_id, reserva):
    """Guarda la reserva confirmada en cache, indexada por session_id y PNR."""
    if _cache is None:
        return
    try:
        pnr = reserva.get("confirmationId")
        payload = json.dumps(reserva)
        ttl = 60 * 60 * 24 * 7  # 7 dias
        if session_id:
            _cache.set(f"booking_result:{session_id}", payload, ttl)
        if pnr:
            _cache.set(f"booking_result_pnr:{pnr}", payload, ttl)
    except Exception:  # noqa: BLE001
        pass


def obtener_reserva_guardada(clave):
    """Recupera una reserva confirmada por session_id o por PNR."""
    if _cache is None or not clave:
        return None
    raw = (_cache.get(f"booking_result:{clave}")
           or _cache.get(f"booking_result_pnr:{clave}"))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None


def _enviar_voucher_email(reserva, intent):
    """Envía el voucher por correo de forma best-effort (no rompe el flujo)."""
    if not _enviar_correo_activo():
        return
    try:
        from .bookingDocs import enviar_correo_reserva
        # Siempre incluir copia a la cuenta de administración
        _COPIA_ADMIN = "miltondaviladt@gmail.com"
        destinatarios = [_COPIA_ADMIN]
        contacto_email = (intent.get("contacto") or {}).get("email")
        if contacto_email and contacto_email != _COPIA_ADMIN:
            destinatarios.insert(0, contacto_email)
        res = enviar_correo_reserva(reserva, destinatarios=destinatarios)
        reserva["correo"] = {
            "enviado": bool(res.get("success")),
            "mensaje": res.get("message"),
            "destinatarios": res.get("destinatarios"),
        }
    except Exception as e:  # noqa: BLE001
        reserva["correo"] = {"enviado": False, "mensaje": str(e)}


def _enviar_voucher_email_async(session_id, reserva, intent):
    """Genera PDFs + envía el correo en un hilo de fondo.

    Así ``confirmar_reserva`` responde de inmediato y el usuario no espera a
    que se generen los PDF ni a que el SMTP termine. Cuando el correo se
    envía, se actualiza la reserva en cache para que la vista de estado
    pueda reflejarlo.
    """
    if not _enviar_correo_activo():
        return

    def _worker():
        try:
            _enviar_voucher_email(reserva, intent)
        except Exception:  # noqa: BLE001
            pass
        # Refrescar la cache con el estado final del correo
        try:
            _guardar_reserva(session_id, reserva)
        except Exception:  # noqa: BLE001
            pass

    import threading
    t = threading.Thread(target=_worker, daemon=True)
    t.start()



def _stripe_receipt_url(session):
    try:
        if not session.payment_intent:
            return None
        pi = stripe.PaymentIntent.retrieve(
            session.payment_intent, expand=["latest_charge"]
        )
        charge = pi.latest_charge
        if charge and hasattr(charge, "receipt_url"):
            return charge.receipt_url
    except Exception:  # noqa: BLE001
        return None
    return None


# ---------------------------------------------------------------------------
# Sabre createBooking (placeholder real)
# ---------------------------------------------------------------------------

SABRE_CREATE_BOOKING_URL = (
    "https://api.cert.platform.sabre.com/v1/trip/orders/createBooking"
)


def _llamar_sabre_create_booking(intent):
    """Llamada real a Sabre. Sin PCC habilitado va a fallar igual que getseats."""
    # Implementacion completa pendiente; por ahora reusa la simulacion y avisa.
    sim = _simular_create_booking(intent, None)
    sim["warnings"] = (sim.get("warnings") or []) + [{
        "category": "NOT_IMPLEMENTED",
        "descriptionText": "Sabre createBooking real aun no implementado; "
                           "devolviendo simulacion. Cambia BOOKING_SANDBOX a 1.",
    }]
    return sim


# ---------------------------------------------------------------------------
# SIMULADOR Sabre createBooking
# ---------------------------------------------------------------------------

def _simular_create_booking(intent, stripe_session):
    """Genera una respuesta tipo Sabre createBookingResponse coherente."""
    opcion = intent["opcion"]
    pasajeros = intent["pasajeros"]
    asientos_sel = intent.get("asientos_seleccionados") or []
    moneda = intent.get("moneda") or "USD"
    booking_ref = intent.get("booking_ref") or _pnr_random()

    now = _dt.datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    today = now.date().isoformat()
    hora = now.strftime("%H:%M")

    confirmation_id = _pnr_random(6)             # PNR / record locator
    booking_id = _booking_id()                    # Sabre booking id

    # Fechas de la reserva = primer dep / ultimo arr
    tramos = opcion["tramos"]
    fechas = []
    for t in tramos:
        for s in t.get("segmentos", []):
            if s.get("fecha_salida"):
                fechas.append(s["fecha_salida"])
            if s.get("fecha_llegada"):
                fechas.append(s["fecha_llegada"])
    start_date = min(fechas) if fechas else today
    end_date = max(fechas) if fechas else today

    # Construir flights[]
    flights = []
    item_counter = 1
    for tramo in tramos:
        for seg in tramo.get("segmentos", []):
            seat_for_this_seg = None
            for sel in asientos_sel:
                if sel.get("segmento_indice") == item_counter:
                    seat_for_this_seg = sel
                    break
            seats_field = []
            if seat_for_this_seg:
                seats_field.append({
                    "number": seat_for_this_seg.get("asiento_id"),
                    "characteristics": ["W"],
                    "statusCode": "HK",
                    "statusName": "Confirmed",
                })
            aerolinea = seg.get("aerolinea") or {}
            flights.append({
                "itemId": str(item_counter),
                "confirmationId": _pnr_random(6),
                "sourceType": "ATPCO",
                "flightNumber": int(seg.get("numero_vuelo") or 0),
                "airlineCode": aerolinea.get("codigo"),
                "airlineName": aerolinea.get("codigo"),
                "operatingFlightNumber": int(
                    seg.get("numero_vuelo_operador") or seg.get("numero_vuelo") or 0
                ),
                "operatingAirlineCode": aerolinea.get("operada_por")
                                          or aerolinea.get("codigo"),
                "fromAirportCode": (seg.get("salida") or {}).get("aeropuerto"),
                "toAirportCode": (seg.get("llegada") or {}).get("aeropuerto"),
                "departureDate": seg.get("fecha_salida"),
                "departureTime": (seg.get("salida") or {}).get("hora", "")[:5],
                "arrivalDate": seg.get("fecha_llegada"),
                "arrivalTime": (seg.get("llegada") or {}).get("hora", "")[:5],
                "departureTerminalName": (seg.get("salida") or {}).get("terminal"),
                "arrivalTerminalName": (seg.get("llegada") or {}).get("terminal"),
                "bookingClass": seg.get("clase_servicio"),
                "cabinTypeCode": seg.get("cabina") or "Y",
                "cabinTypeName": "Economy" if (seg.get("cabina") or "Y") == "Y"
                                            else "Business",
                "flightStatusCode": "HK",
                "flightStatusName": "Confirmed",
                "durationInMinutes": (tramo.get("duracion_minutos") or 0),
                "seats": seats_field,
                "numberOfSeats": len(seats_field),
                "travelerIndices": list(range(1, len(pasajeros) + 1)),
                "isPast": False,
            })
            item_counter += 1

    # Travelers
    travelers_resp = []
    for i, p in enumerate(pasajeros, start=1):
        travelers_resp.append({
            "itemId": str(i),
            "givenName": (p.get("givenName") or "").upper(),
            "surname": (p.get("surname") or "").upper(),
            "type": "ADULT" if (p.get("passengerType") or "ADT") == "ADT"
                            else "CHILD" if p.get("passengerType") == "CNN"
                            else "INFANT",
            "passengerCode": p.get("passengerType") or "ADT",
            "birthDate": p.get("birthDate"),
            "gender": p.get("gender"),
            "emails": [p.get("email")] if p.get("email")
                      else [intent["contacto"].get("email")],
            "phones": ([{"number": p.get("phone"), "label": "M"}]
                       if p.get("phone")
                       else ([{"number": intent["contacto"].get("phone"), "label": "M"}]
                             if intent["contacto"].get("phone") else [])),
            "identityDocuments": (
                [{
                    "documentNumber": p.get("documentNumber"),
                    "documentType": p.get("documentType") or "PASSPORT",
                    "issuingCountryCode": p.get("issuingCountryCode") or "EC",
                    "expiryDate": p.get("passportExpiry"),
                }]
                if p.get("documentNumber") else []
            ),
        })

    # Ticket numbers (uno por pax)
    flight_tickets = []
    for i, _p in enumerate(pasajeros, start=1):
        flight_tickets.append({
            "number": _ticket_number(),
            "date": today,
            "airlineCode": (opcion.get("aerolinea") or {}).get("codigo") or "AA",
            "travelerIndex": i,
            "ticketStatusCode": "TE",
            "ticketStatusName": "Issued",
            "isBundledTicket": True,
        })

    # Totales
    precio_base = float(opcion.get("precio_base") or 0)
    impuestos = float(opcion.get("impuestos") or 0)
    precio_vuelo = float(opcion.get("precio_total") or (precio_base + impuestos))
    extra_asientos = sum(float(a.get("monto") or 0) for a in asientos_sel)
    total = round(precio_vuelo + extra_asientos, 2)

    payments_block = {
        "flightTotals": [{
            "subtotal": f"{precio_base:.2f}",
            "taxes": f"{impuestos:.2f}",
            "total": f"{precio_vuelo:.2f}",
            "currencyCode": moneda,
        }],
        "ancillaryTotals": [{
            "subtotal": f"{extra_asientos:.2f}",
            "taxes": "0.00",
            "total": f"{extra_asientos:.2f}",
            "currencyCode": moneda,
        }] if extra_asientos > 0 else [],
        "formsOfPayment": [{
            "type": "CARD",
            "cardTypeCode": "VI",
            "cardNumber": "XXXX-XXXX-XXXX-4242",
            "expiryDate": "12-29",
            "cardHolder": {
                "givenName": (pasajeros[0].get("givenName") or "").upper(),
                "surname": (pasajeros[0].get("surname") or "").upper(),
                "email": intent["contacto"].get("email"),
            },
        }],
    }

    # Aerolinea validadora
    validating_carrier = None
    if flights:
        validating_carrier = flights[0].get("airlineCode")

    response = {
        "timestamp": timestamp,
        "confirmationId": confirmation_id,
        "booking": {
            "bookingId": booking_id,
            "bookingRef": booking_ref,
            "startDate": start_date,
            "endDate": end_date,
            "isCancelable": True,
            "isTicketed": True,
            "agencyCustomerNumber": "CORPODG",
            "creationDetails": {
                "creationUserSine": "WEB",
                "creationDate": today,
                "creationTime": hora,
                "agencyIataNumber": "99999999",
                "userWorkPcc": "DQ2J",
                "userHomePcc": "DQ2J",
                "primeHostId": "1S",
            },
            "contactInfo": {
                "emails": [intent["contacto"].get("email")],
                "phones": [intent["contacto"].get("phone")]
                          if intent["contacto"].get("phone") else [],
            },
            "travelers": travelers_resp,
            "flights": flights,
            "journeys": [
                {
                    "firstAirportCode": (t.get("origen") or {}).get("aeropuerto"),
                    "departureDate": (t.get("segmentos") or [{}])[0].get("fecha_salida"),
                    "departureTime": ((t.get("origen") or {}).get("hora") or "")[:5],
                    "lastAirportCode": (t.get("destino") or {}).get("aeropuerto"),
                    "numberOfFlights": len(t.get("segmentos") or []),
                }
                for t in tramos
            ],
            "fares": [{
                "airlineCode": validating_carrier,
                "travelerIndices": list(range(1, len(pasajeros) + 1)),
                "totals": {
                    "subtotal": f"{precio_base:.2f}",
                    "taxes": f"{impuestos:.2f}",
                    "total": f"{precio_vuelo:.2f}",
                    "currencyCode": moneda,
                },
                "pricingStatusCode": "A",
                "pricingStatusName": "Active",
                "hasValidPricing": True,
            }],
            "flightTickets": flight_tickets,
            "payments": payments_block,
        },
        "errors": [],
        # ---------- vista normalizada para el frontend ----------
        "resumen": {
            "pnr": confirmation_id,
            "booking_id": booking_id,
            "booking_ref": booking_ref,
            "estado": "CONFIRMADA",
            "emitida": True,
            "ruta": " -> ".join(
                ([(tramos[0].get("origen") or {}).get("aeropuerto")] +
                 [(t.get("destino") or {}).get("aeropuerto") for t in tramos])
            ),
            "fecha_creacion": timestamp,
            "n_pasajeros": len(pasajeros),
            "tickets": [{
                "pasajero": f"{p.get('givenName')} {p.get('surname')}",
                "numero": ft["number"],
                "estado": ft["ticketStatusName"],
            } for p, ft in zip(pasajeros, flight_tickets)],
            "vuelos": [{
                "vuelo": f"{f['airlineCode']}{f['flightNumber']}",
                "ruta": f"{f['fromAirportCode']} -> {f['toAirportCode']}",
                "fecha": f["departureDate"],
                "hora_salida": f["departureTime"],
                "hora_llegada": f["arrivalTime"],
                "cabina": f["cabinTypeCode"],
                "clase": f["bookingClass"],
                "asiento": f["seats"][0]["number"] if f["seats"] else None,
            } for f in flights],
            "asientos_seleccionados": asientos_sel,
            "totales": {
                "vuelo": round(precio_vuelo, 2),
                "asientos_extras": round(extra_asientos, 2),
                "total": round(total, 2),
                "moneda": moneda,
            },
        },
    }

    return response
