"""Generación de documentos de reserva (voucher / boletos de vuelo).

Toma la respuesta de ``confirmar_reserva`` / ``_simular_create_booking``
(estructura tipo Sabre ``createBookingResponse`` + ``resumen``) y construye:

  * ``render_voucher_html(reserva, modo=...)``  -> HTML autocontenido con
        - tarjetas estilo "boarding pass" por cada vuelo (logo de la
          aerolínea, ruta, ciudades, horas, terminal, cabina, clase,
          asiento, estado),
        - bloque de pasajeros,
        - bloque de boletos emitidos (ticket numbers),
        - factura / totales,
        - datos del pago (Stripe).
  * ``generar_voucher_pdf(reserva)``            -> bytes PDF (xhtml2pdf).
  * ``enviar_correo_reserva(reserva, ...)``     -> envía el correo con el
        HTML embebido + el PDF adjunto.

El mismo HTML sirve para:
  - el correo electrónico (``modo='email'`` -> logo CorpoDG vía ``cid``),
  - la vista imprimible del navegador (``modo='web'`` -> logo en base64),
  - el PDF (``modo='pdf'`` -> logo en base64 + ``link_callback``).
"""

import base64
import io
import os
import tempfile

try:
    from django.conf import settings as _settings
except Exception:  # pragma: no cover
    _settings = None


# Logos de aerolíneas (fallback si la BD no tiene logo_url).
# avs.io expone logos públicos por código IATA.
_AVS_LOGO = "https://pics.avs.io/200/80/{code}.png"

_GOLD = "#B8860B"
_DARK = "#1f1a3d"


# Ícono de avión. En PDF se usa el SVG vectorial (lo rasteriza svglib);
# en web/email se usa el glyph Unicode como TEXTO (las data-URI SVG las
# bloquea Gmail y varios clientes de correo).
_AVION_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" '
    'viewBox="0 0 24 24"><path fill="{color}" d="M21 16v-2l-8-5V3.5C13 2.67 '
    '12.33 2 11.5 2S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5'
    'L13 19v-5.5l8 2.5z"/></svg>'
)


def _avion_datauri(color=_GOLD):
    svg = _AVION_SVG.format(color=color)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _avion_img(modo="web", color=_GOLD, size=30):
    """Devuelve el ícono de avión apropiado para el medio.

    - PDF  -> <img> con el SVG embebido (svglib lo renderiza).
    - web/email -> glyph Unicode como texto (compatible con Gmail).
    """
    if modo == "pdf":
        return (
            f'<img src="{_avion_datauri(color)}" alt="vuelo" '
            f'style="width:{size}px;height:{size}px;" />'
        )
    return (
        f'<span style="font-size:{size}px;line-height:1;color:{color};">'
        f'&#9992;</span>'
    )


# ---------------------------------------------------------------------------
# Helpers de datos (logos / aeropuertos)
# ---------------------------------------------------------------------------

def _logo_aerolinea(code):
    """Devuelve la URL del logo de la aerolínea (BD o fallback público)."""
    if not code:
        return ""
    try:
        from .models import Aerolinea
        aero = Aerolinea.objects.filter(codigo_iata=code).first()
        if aero and (aero.logo_url or aero.brandmark_url):
            return aero.logo_url or aero.brandmark_url
    except Exception:
        pass
    return _AVS_LOGO.format(code=code)


def _nombre_aerolinea(code, fallback=None):
    if not code:
        return fallback or ""
    try:
        from .models import Aerolinea
        aero = Aerolinea.objects.filter(codigo_iata=code).first()
        if aero and aero.nombre:
            return aero.nombre
    except Exception:
        pass
    return fallback or code


def _info_aeropuerto(code):
    """(codigo, ciudad/nombre) para un código IATA."""
    if not code:
        return ("", "")
    try:
        from .models import Aeropuerto
        ap = Aeropuerto.objects.filter(codigo_iata=code).first()
        if ap:
            ciudad = (ap.ciudad.nombre if ap.ciudad else ap.nombre_ciudad) or ap.nombre
            return (code, ciudad or "")
    except Exception:
        pass
    return (code, "")


def _corpodg_logo_datauri():
    """Logo de CorpoDG embebido en base64 (para web / PDF)."""
    try:
        base_dir = getattr(_settings, "BASE_DIR", None) if _settings else None
        if not base_dir:
            return ""
        logo_path = os.path.join(base_dir, "servicios", "static", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode("ascii")
            return f"data:image/png;base64,{b64}"
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Construcción del contexto a partir de la reserva
# ---------------------------------------------------------------------------

def _contexto(reserva):
    booking = reserva.get("booking") or {}
    resumen = reserva.get("resumen") or {}
    pago = reserva.get("pago") or {}

    pnr = reserva.get("confirmationId") or resumen.get("pnr") or "------"
    flights = booking.get("flights") or []
    travelers = booking.get("travelers") or []
    tickets = booking.get("flightTickets") or []
    totales = resumen.get("totales") or {}
    moneda = totales.get("moneda") or pago.get("moneda") or "USD"

    # Pasajeros legibles
    pasajeros = []
    for t in travelers:
        nombre = f"{t.get('givenName', '')} {t.get('surname', '')}".strip()
        if nombre:
            pasajeros.append(nombre)

    # Boletos emitidos (pasajero + número + estado)
    boletos = []
    for tk in tickets:
        idx = tk.get("travelerIndex")
        nombre = ""
        if idx and 1 <= idx <= len(pasajeros):
            nombre = pasajeros[idx - 1]
        boletos.append({
            "pasajero": nombre,
            "numero": tk.get("number"),
            "estado": tk.get("ticketStatusName") or "Issued",
            "aerolinea": tk.get("airlineCode"),
        })

    # Vuelos enriquecidos
    vuelos = []
    for f in flights:
        code = f.get("airlineCode") or ""
        origen_cod, origen_ciudad = _info_aeropuerto(f.get("fromAirportCode"))
        destino_cod, destino_ciudad = _info_aeropuerto(f.get("toAirportCode"))
        seats = f.get("seats") or []
        vuelos.append({
            "aerolinea_codigo": code,
            "aerolinea_nombre": _nombre_aerolinea(code, f.get("airlineName")),
            "logo": _logo_aerolinea(code),
            "numero": f"{code}{f.get('flightNumber', '')}",
            "origen_codigo": origen_cod,
            "origen_ciudad": origen_ciudad,
            "destino_codigo": destino_cod,
            "destino_ciudad": destino_ciudad,
            "fecha_salida": f.get("departureDate") or "",
            "hora_salida": f.get("departureTime") or "",
            "fecha_llegada": f.get("arrivalDate") or "",
            "hora_llegada": f.get("arrivalTime") or "",
            "terminal_salida": f.get("departureTerminalName") or "-",
            "terminal_llegada": f.get("arrivalTerminalName") or "-",
            "cabina": f.get("cabinTypeName") or f.get("cabinTypeCode") or "Economy",
            "clase": f.get("bookingClass") or "-",
            "asiento": seats[0].get("number") if seats else "-",
            "estado": f.get("flightStatusName") or "Confirmed",
        })

    ruta = resumen.get("ruta") or " -> ".join(
        [v["origen_codigo"] for v in vuelos[:1]]
        + [v["destino_codigo"] for v in vuelos]
    )

    # Agrupar vuelos por trayecto (ida / vuelta / tramos) usando journeys.
    journeys = booking.get("journeys") or []
    grupos = []
    idx = 0
    if journeys:
        total_j = len(journeys)
        for ji, j in enumerate(journeys):
            n = int(j.get("numberOfFlights") or 1)
            seg = vuelos[idx:idx + n]
            idx += n
            if not seg:
                continue
            if total_j == 1:
                titulo = "Vuelo"
            elif total_j == 2:
                titulo = "Vuelo de ida" if ji == 0 else "Vuelo de regreso"
            else:
                titulo = f"Tramo {ji + 1}"
            grupos.append({
                "titulo": titulo,
                "ruta": f'{seg[0]["origen_codigo"]} → {seg[-1]["destino_codigo"]}',
                "fecha": seg[0]["fecha_salida"],
                "vuelos": seg,
            })
    if idx < len(vuelos):  # vuelos sin journey asociado
        seg = vuelos[idx:]
        grupos.append({
            "titulo": "Vuelo" if not grupos else "Otros vuelos",
            "ruta": f'{seg[0]["origen_codigo"]} → {seg[-1]["destino_codigo"]}',
            "fecha": seg[0]["fecha_salida"],
            "vuelos": seg,
        })
    if not grupos and vuelos:
        grupos = [{
            "titulo": "Itinerario",
            "ruta": ruta,
            "fecha": vuelos[0]["fecha_salida"],
            "vuelos": vuelos,
        }]

    es_ida_vuelta = len([g for g in grupos if g["titulo"] in
                         ("Vuelo de ida", "Vuelo de regreso")]) == 2

    return {
        "pnr": pnr,
        "ruta": ruta,
        "estado": resumen.get("estado") or "CONFIRMADA",
        "emitida": booking.get("isTicketed", True),
        "sandbox": bool(reserva.get("sandbox")),
        "pasajeros": pasajeros,
        "boletos": boletos,
        "vuelos": vuelos,
        "grupos": grupos,
        "es_ida_vuelta": es_ida_vuelta,
        "moneda": moneda,
        "total_vuelo": totales.get("vuelo", 0),
        "total_asientos": totales.get("asientos_extras", 0),
        "total": totales.get("total", pago.get("monto", 0)),
        "pago": {
            "estado": (pago.get("estado") or "paid"),
            "monto": pago.get("monto", totales.get("total", 0)),
            "moneda": pago.get("moneda") or moneda,
            "proveedor": (pago.get("proveedor") or "stripe").upper(),
            "recibo_url": pago.get("recibo_url"),
        },
    }


# ---------------------------------------------------------------------------
# Render HTML
# ---------------------------------------------------------------------------

def _tarjeta_vuelo(v, modo="web"):
    """HTML de una tarjeta estilo boarding pass para un vuelo."""
    logo_img = (
        f'<img src="{v["logo"]}" alt="{v["aerolinea_codigo"]}" '
        f'style="max-height:34px;max-width:120px;" />'
        if v["logo"] else f'<strong>{v["aerolinea_codigo"]}</strong>'
    )
    origen_ciudad = f'<div style="font-size:11px;color:#666;">{v["origen_ciudad"]}</div>' if v["origen_ciudad"] else ""
    destino_ciudad = f'<div style="font-size:11px;color:#666;">{v["destino_ciudad"]}</div>' if v["destino_ciudad"] else ""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e3e3ef;border-radius:10px;margin-bottom:14px;background:#ffffff;">
      <tr>
        <td style="background:{_DARK};padding:10px 16px;border-top-left-radius:10px;border-top-right-radius:10px;">
          <table width="100%"><tr>
            <td style="background:#ffffff;border-radius:6px;padding:4px 8px;">{logo_img}</td>
            <td align="right" style="color:#ffffff;font-weight:bold;font-size:16px;letter-spacing:1px;">{v["numero"]}</td>
          </tr></table>
        </td>
      </tr>
      <tr>
        <td style="padding:16px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="38%" valign="top">
                <div style="font-size:26px;font-weight:bold;color:{_DARK};">{v["origen_codigo"]}</div>
                {origen_ciudad}
                <div style="font-size:13px;color:#333;margin-top:4px;">{v["fecha_salida"]}</div>
                <div style="font-size:18px;font-weight:bold;color:{_GOLD};">{v["hora_salida"]}</div>
                <div style="font-size:10px;color:#888;">Terminal {v["terminal_salida"]}</div>
              </td>
              <td width="24%" align="center" valign="middle">{_avion_img(modo, _GOLD, 26)}</td>
              <td width="38%" valign="top" align="right">
                <div style="font-size:26px;font-weight:bold;color:{_DARK};">{v["destino_codigo"]}</div>
                {destino_ciudad}
                <div style="font-size:13px;color:#333;margin-top:4px;">{v["fecha_llegada"]}</div>
                <div style="font-size:18px;font-weight:bold;color:{_GOLD};">{v["hora_llegada"]}</div>
                <div style="font-size:10px;color:#888;">Terminal {v["terminal_llegada"]}</div>
              </td>
            </tr>
          </table>
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;border-top:1px dashed #d0d0e0;padding-top:10px;">
            <tr style="font-size:11px;color:#666;">
              <td><strong style="color:#333;">Aerolínea</strong><br/>{v["aerolinea_nombre"]}</td>
              <td><strong style="color:#333;">Cabina</strong><br/>{v["cabina"]}</td>
              <td><strong style="color:#333;">Clase</strong><br/>{v["clase"]}</td>
              <td><strong style="color:#333;">Asiento</strong><br/>{v["asiento"]}</td>
              <td><strong style="color:#333;">Estado</strong><br/>{v["estado"]}</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """


def render_voucher_html(reserva, modo="web"):
    """Construye el HTML completo del voucher.

    modo:
      - 'email' -> logo CorpoDG vía cid:logo_corpodg (lo adjunta el correo).
      - 'web' / 'pdf' -> logo CorpoDG embebido en base64.
    """
    ctx = _contexto(reserva)

    if modo == "email":
        logo_src = "cid:logo_corpodg"
    else:
        logo_src = _corpodg_logo_datauri()

    logo_html = (
        f'<img src="{logo_src}" alt="CorpoDG" style="max-width:180px;height:auto;" />'
        if logo_src else '<span style="color:#fff;font-size:22px;font-weight:bold;">CorpoDG</span>'
    )

    banner_sandbox = ""
    if ctx["sandbox"]:
        banner_sandbox = (
            '<div style="text-align:center;margin:0 0 16px 0;">'
            '<span style="display:inline-block;background:#fff7e6;color:#b26a00;'
            'border:1px solid #ffd591;border-radius:20px;padding:6px 16px;'
            'font-size:12px;font-weight:bold;">Modo demostración — reserva simulada (sandbox)</span>'
            "</div>"
        )

    tarjetas = ""
    for g in ctx["grupos"]:
        meta = " · ".join([x for x in (g.get("ruta"), g.get("fecha")) if x])
        tarjetas += (
            f'<div style="margin:4px 0 10px 0;">'
            f'<span style="display:inline-block;background:{_DARK};color:#fff;'
            f'font-size:12px;font-weight:bold;padding:5px 14px;border-radius:14px;">'
            f'{g["titulo"]}</span>'
            f'<span style="color:#888;font-size:12px;margin-left:8px;">{meta}</span>'
            f"</div>"
        )
        tarjetas += "".join(_tarjeta_vuelo(v, modo) for v in g["vuelos"])

    filas_pasajeros = "".join(
        f'<tr><td style="padding:6px 0;color:#333;">&#128100; {p}</td></tr>'
        for p in ctx["pasajeros"]
    )

    filas_boletos = "".join(
        f"""<tr>
            <td style="padding:8px;border-bottom:1px solid #eee;color:#333;">{b['pasajero']}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;font-family:monospace;color:#333;">{b['numero']}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">
              <span style="background:#e6f7ed;color:#1a7f43;padding:2px 8px;border-radius:10px;font-size:11px;">{b['estado']}</span>
            </td>
        </tr>"""
        for b in ctx["boletos"]
    )

    fila_asientos = ""
    if ctx["total_asientos"]:
        fila_asientos = (
            f'<tr><td style="padding:6px 0;color:#555;">Asientos extra</td>'
            f'<td align="right" style="padding:6px 0;color:#333;font-weight:bold;">'
            f'{ctx["moneda"]} {float(ctx["total_asientos"]):.2f}</td></tr>'
        )

    recibo_link = ""
    if ctx["pago"]["recibo_url"]:
        recibo_link = (
            f'<div style="margin-top:8px;"><a href="{ctx["pago"]["recibo_url"]}" '
            f'style="color:{_GOLD};font-size:12px;">Ver recibo de pago</a></div>'
        )

    # En PDF el contenedor ocupa TODO el ancho de la página (A4): se elimina
    # el wrapper de centrado (<td align="center"> + tabla anidada), porque
    # xhtml2pdf encoge la tabla interna a su contenido y se veía diminuta.
    # En web/email se mantiene centrado con ancho fijo agradable.
    if modo == "pdf":
        wrap_open = (
            '<table width="100%" cellpadding="0" cellspacing="0" '
            'style="width:100%;">'
        )
        wrap_close = "</table>"
    else:
        wrap_open = (
            '<table width="100%" cellpadding="0" cellspacing="0" '
            'style="background:#eef0f5;padding:24px 0;">'
            '<tr><td align="center">'
            '<table width="640" cellpadding="0" cellspacing="0" '
            'style="max-width:640px;">'
        )
        wrap_close = "</table></td></tr></table>"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>Reserva {ctx['pnr']} - CorpoDG</title>
  <style>
    @page {{ size: A4 portrait; margin: 1cm; }}
    body {{ margin:0; padding:0; }}
  </style>
</head>
<body style="margin:0;padding:0;background:#eef0f5;font-family:Arial,Helvetica,sans-serif;">
  {wrap_open}

        <!-- Header -->
        <tr><td style="background:{_GOLD};border-radius:12px 12px 0 0;padding:22px;text-align:center;">
          {logo_html}
          <div style="color:#fff;font-size:13px;margin-top:6px;">Confirmación de reserva</div>
        </td></tr>

        <!-- Estado -->
        <tr><td style="background:#fff;padding:26px 24px 6px 24px;text-align:center;">
          <div style="width:56px;height:56px;line-height:56px;border-radius:50%;background:#16a34a;color:#fff;font-size:28px;margin:0 auto 10px auto;">&#10003;</div>
          <div style="font-size:22px;font-weight:bold;color:{_DARK};">¡Reserva confirmada!</div>
          <div style="color:#667;font-size:14px;margin-top:4px;">Tus boletos fueron emitidos correctamente.</div>
          <div style="color:#8a6d1a;background:#fdf6e3;border:1px solid #e5d9a8;border-radius:8px;padding:8px 14px;margin:12px auto 0 auto;font-size:12px;max-width:420px;">
            Para realizar una cancelación de tu reserva debes contactarte directamente con la empresa.
          </div>
        </td></tr>

        <tr><td style="background:#fff;padding:10px 24px 0 24px;">{banner_sandbox}</td></tr>

        <!-- PNR + Pago -->
        <tr><td style="background:#fff;padding:0 24px 18px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="50%" valign="top" style="padding-right:8px;">
                <table width="100%" style="background:{_DARK};border-radius:10px;">
                  <tr><td style="padding:18px;text-align:center;">
                    <div style="color:#b9b6d6;font-size:12px;">Código de reserva (PNR)</div>
                    <div style="color:#fff;font-size:30px;font-weight:bold;letter-spacing:4px;">{ctx['pnr']}</div>
                    <div style="color:#cfcce6;font-size:13px;margin-top:4px;">{ctx['ruta']}</div>
                    <div style="margin-top:8px;"><span style="background:#16a34a;color:#fff;padding:3px 12px;border-radius:12px;font-size:11px;">{ctx['estado']}</span></div>
                  </td></tr>
                </table>
              </td>
              <td width="50%" valign="top" style="padding-left:8px;">
                <table width="100%" style="border:1px solid #e3e3ef;border-radius:10px;">
                  <tr><td style="padding:16px;">
                    <div style="font-size:15px;font-weight:bold;color:{_DARK};margin-bottom:8px;">Pago</div>
                    <table width="100%" style="font-size:13px;color:#444;">
                      <tr><td style="padding:3px 0;">Estado</td><td align="right" style="font-weight:bold;color:#16a34a;">{ctx['pago']['estado'].upper()}</td></tr>
                      <tr><td style="padding:3px 0;">Monto</td><td align="right" style="font-weight:bold;">{ctx['pago']['moneda']} {float(ctx['pago']['monto']):.2f}</td></tr>
                      <tr><td style="padding:3px 0;">Proveedor</td><td align="right" style="font-weight:bold;">{ctx['pago']['proveedor']}</td></tr>
                    </table>
                    {recibo_link}
                  </td></tr>
                </table>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Itinerario / boarding passes -->
        <tr><td style="background:#fff;padding:6px 24px 0 24px;">
          <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:12px;">Itinerario</div>
          {tarjetas}
        </td></tr>

        <!-- Boletos emitidos -->
        <tr><td style="background:#fff;padding:6px 24px 0 24px;">
          <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:10px;">Boletos emitidos</div>
          <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eee;border-radius:8px;">
            <tr style="background:#f7f7fb;font-size:12px;color:#666;">
              <td style="padding:8px;">Pasajero</td><td style="padding:8px;">N° de boleto</td><td style="padding:8px;">Estado</td>
            </tr>
            {filas_boletos}
          </table>
        </td></tr>

        <!-- Totales + Pasajeros -->
        <tr><td style="background:#fff;padding:18px 24px 24px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="55%" valign="top" style="padding-right:8px;">
                <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:10px;">Totales</div>
                <table width="100%" style="font-size:14px;">
                  <tr><td style="padding:6px 0;color:#555;">Vuelo</td><td align="right" style="padding:6px 0;color:#333;font-weight:bold;">{ctx['moneda']} {float(ctx['total_vuelo']):.2f}</td></tr>
                  {fila_asientos}
                  <tr><td style="padding:10px 0;border-top:2px solid #222;font-weight:bold;color:{_DARK};">Total</td>
                      <td align="right" style="padding:10px 0;border-top:2px solid #222;font-weight:bold;font-size:16px;color:{_DARK};">{ctx['moneda']} {float(ctx['total']):.2f}</td></tr>
                </table>
              </td>
              <td width="45%" valign="top" style="padding-left:8px;">
                <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:10px;">Pasajeros</div>
                <table width="100%" style="font-size:14px;">{filas_pasajeros}</table>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:{_DARK};border-radius:0 0 12px 12px;padding:18px;text-align:center;">
          <div style="color:#fff;font-size:12px;">© 2026 CorpoDG — Todos los derechos reservados</div>
          <div style="color:#b9b6d6;font-size:11px;margin-top:4px;">Este documento es tu comprobante de reserva. Consérvalo para el check-in.</div>
        </td></tr>

      {wrap_close}
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _link_callback(uri, rel):
    """Resuelve recursos (logos remotos / SVG / estáticos) para xhtml2pdf."""
    # SVG embebido como data-URI -> escribir a .svg temporal (lo rasteriza svglib)
    if uri.startswith("data:image/svg+xml"):
        try:
            header, _, payload = uri.partition(",")
            if "base64" in header:
                raw = base64.b64decode(payload)
            else:
                from urllib.parse import unquote
                raw = unquote(payload).encode("utf-8")
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".svg")
            tmp.write(raw)
            tmp.close()
            return tmp.name
        except Exception:
            return uri
    if uri.startswith("data:"):
        return uri
    if uri.startswith("http://") or uri.startswith("https://"):
        try:
            import requests
            resp = requests.get(uri, timeout=8)
            if resp.status_code == 200 and resp.content:
                ctype = resp.headers.get("Content-Type", "")
                ext = ".png"
                if "jpeg" in ctype or "jpg" in ctype:
                    ext = ".jpg"
                elif "svg" in ctype:
                    ext = ".svg"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                tmp.write(resp.content)
                tmp.close()
                return tmp.name
        except Exception:
            return uri
        return uri
    # Estáticos locales
    try:
        if _settings is not None:
            static_url = getattr(_settings, "STATIC_URL", "/static/")
            static_root = getattr(_settings, "STATIC_ROOT", None)
            if static_root and uri.startswith(static_url):
                path = os.path.join(str(static_root), uri.replace(static_url, ""))
                if os.path.exists(path):
                    return path
    except Exception:
        pass
    return uri


def generar_voucher_pdf(reserva):
    """Genera el PDF del voucher. Devuelve bytes o None si falla."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return None
    html = render_voucher_html(reserva, modo="pdf")
    buffer = io.BytesIO()
    try:
        result = pisa.CreatePDF(
            src=html, dest=buffer, encoding="utf-8", link_callback=_link_callback
        )
    except Exception:
        return None
    if result.err:
        return None
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Boletos estilo aerolínea (PDF aparte, "emitido por la aerolínea")
# ---------------------------------------------------------------------------

def _barcode_html(value):
    """Banda tipo código de barras (decorativa) como una sola imagen SVG.

    Se usa un único <img> con un SVG embebido en lugar de una tabla con
    muchas celdas: xhtml2pdf ignora el cellpadding y aplica un padding por
    celda que, con decenas de columnas, desborda el ancho de la página y
    rompía la generación del PDF (availWidth negativo). Una sola imagen SVG
    se renderiza bien tanto en el PDF (vía svglib) como en la vista web.
    """
    value = (value or "000000000000")[:24]
    alto = 44
    x = 0
    barras = []
    for ch in value:
        w = (ord(ch) % 3) + 2  # 2..4 px de barra negra
        barras.append(
            f'<rect x="{x}" y="0" width="{w}" height="{alto}" fill="#111"/>'
        )
        x += w + 2  # 2px de espacio blanco
    ancho = max(x, 1)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" '
        f'height="{alto}" viewBox="0 0 {ancho} {alto}">'
        f'<rect x="0" y="0" width="{ancho}" height="{alto}" fill="#ffffff"/>'
        + "".join(barras)
        + "</svg>"
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'alt="barcode" style="height:{alto}px;width:{ancho}px;" />'
    )


def _ticket_aerolinea(pnr, pax, ticket_num, v, modo="web"):
    """Una tarjeta de embarque estilo aerolínea para (pasajero, vuelo)."""
    logo_img = (
        f'<img src="{v["logo"]}" alt="{v["aerolinea_codigo"]}" '
        f'style="max-height:40px;max-width:150px;" />'
        if v["logo"] else
        f'<span style="font-size:22px;font-weight:bold;color:{_DARK};">{v["aerolinea_codigo"]}</span>'
    )
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid #d8d8e2;border-radius:12px;margin-bottom:18px;background:#fff;">
      <tr>
        <td style="padding:14px 18px;border-bottom:2px dashed #d8d8e2;">
          <table width="100%"><tr>
            <td valign="middle">{logo_img}</td>
            <td align="right" valign="middle">
              <div style="font-size:11px;color:#888;letter-spacing:2px;">TARJETA DE EMBARQUE</div>
              <div style="font-size:15px;font-weight:bold;color:{_DARK};letter-spacing:1px;">BOARDING PASS</div>
            </td>
          </tr></table>
        </td>
      </tr>
      <tr>
        <td style="padding:16px 18px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td colspan="3" style="padding-bottom:10px;">
                <div style="font-size:10px;color:#888;letter-spacing:1px;">PASAJERO / PASSENGER</div>
                <div style="font-size:20px;font-weight:bold;color:{_DARK};">{pax}</div>
              </td>
            </tr>
            <tr>
              <td width="40%" valign="top">
                <div style="font-size:30px;font-weight:bold;color:{_DARK};">{v["origen_codigo"]}</div>
                <div style="font-size:11px;color:#666;">{v["origen_ciudad"]}</div>
              </td>
              <td width="20%" align="center" valign="middle">{_avion_img(modo, _GOLD, 24)}</td>
              <td width="40%" valign="top" align="right">
                <div style="font-size:30px;font-weight:bold;color:{_DARK};">{v["destino_codigo"]}</div>
                <div style="font-size:11px;color:#666;">{v["destino_ciudad"]}</div>
              </td>
            </tr>
          </table>

          <table width="100%" cellpadding="0" cellspacing="0"
                 style="margin-top:14px;border-top:1px solid #eee;padding-top:12px;font-size:12px;">
            <tr>
              <td><div style="color:#888;font-size:10px;">VUELO</div><div style="font-weight:bold;color:{_DARK};">{v["numero"]}</div></td>
              <td><div style="color:#888;font-size:10px;">FECHA</div><div style="font-weight:bold;color:{_DARK};">{v["fecha_salida"]}</div></td>
              <td><div style="color:#888;font-size:10px;">EMBARQUE</div><div style="font-weight:bold;color:{_GOLD};">{v["hora_salida"]}</div></td>
              <td><div style="color:#888;font-size:10px;">TERMINAL</div><div style="font-weight:bold;color:{_DARK};">{v["terminal_salida"]}</div></td>
              <td><div style="color:#888;font-size:10px;">ASIENTO</div><div style="font-weight:bold;color:{_DARK};">{v["asiento"]}</div></td>
              <td><div style="color:#888;font-size:10px;">CLASE</div><div style="font-weight:bold;color:{_DARK};">{v["clase"]}</div></td>
            </tr>
          </table>

          <table width="100%" cellpadding="0" cellspacing="0"
                 style="margin-top:10px;font-size:11px;color:#555;">
            <tr>
              <td>Llegada estimada: <strong>{v["hora_llegada"]}</strong> ({v["fecha_llegada"]}) · Terminal {v["terminal_llegada"]}</td>
              <td align="right">Cabina: <strong>{v["cabina"]}</strong></td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:0 18px 16px 18px;">
          <table width="100%" style="border-top:2px dashed #d8d8e2;padding-top:12px;">
            <tr>
              <td valign="middle">
                <div style="font-size:10px;color:#888;">N° BOLETO / E-TICKET</div>
                <div style="font-family:monospace;font-size:14px;font-weight:bold;color:{_DARK};">{ticket_num}</div>
                <div style="font-size:10px;color:#888;margin-top:6px;">PNR / RESERVA</div>
                <div style="font-family:monospace;font-size:14px;font-weight:bold;letter-spacing:3px;color:{_DARK};">{pnr}</div>
              </td>
              <td align="right" valign="middle">
                {_barcode_html(ticket_num + pnr)}
                <div style="font-family:monospace;font-size:10px;color:#444;letter-spacing:2px;margin-top:4px;">{ticket_num}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """


def render_boletos_html(reserva, modo="web"):
    """HTML de los boletos estilo aerolínea (sin branding CorpoDG)."""
    ctx = _contexto(reserva)
    pnr = ctx["pnr"]

    # ticket por pasajero
    ticket_por_pax = {}
    for b in ctx["boletos"]:
        if b.get("pasajero"):
            ticket_por_pax[b["pasajero"]] = b.get("numero")
    fallback_ticket = (ctx["boletos"][0]["numero"]
                       if ctx["boletos"] else "0000000000000")

    pasajeros = ctx["pasajeros"] or ["PASAJERO"]

    bloques = []
    for pax in pasajeros:
        tnum = ticket_por_pax.get(pax, fallback_ticket)
        for g in ctx["grupos"]:
            for v in g["vuelos"]:
                bloques.append(_ticket_aerolinea(pnr, pax, tnum, v, modo))

    banner = ""
    if ctx["sandbox"]:
        banner = (
            '<div style="text-align:center;margin-bottom:14px;">'
            '<span style="display:inline-block;background:#fff7e6;color:#b26a00;'
            'border:1px solid #ffd591;border-radius:18px;padding:5px 14px;'
            'font-size:11px;font-weight:bold;">Documento de demostración (sandbox)</span>'
            "</div>"
        )

    if modo == "pdf":
        cabecera = (
            '<div style="font-size:18px;font-weight:bold;color:#1f1a3d;margin-bottom:4px;">Boletos electrónicos</div>'
            '<div style="font-size:12px;color:#777;margin-bottom:14px;">Conserva este documento y preséntalo en el aeropuerto junto con tu identificación.</div>'
        )
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" /><title>Boletos {pnr}</title>
  <style>
    @page {{ size: A4 portrait; margin: 1cm; }}
    body {{ margin:0; padding:0; }}
  </style>
</head>
<body style="margin:0;padding:0;background:#fff;font-family:Arial,Helvetica,sans-serif;">
  {cabecera}
  {banner}
  {''.join(bloques)}
</body>
</html>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" /><title>Boletos {pnr}</title>
  <style>
    @page {{ size: A4 portrait; margin: 1cm; }}
    body {{ margin:0; padding:0; }}
  </style>
</head>
<body style="margin:0;padding:0;background:#eef0f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#eef0f5;padding:22px 0;">
    <tr><td align="center">
      <table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;">
        <tr><td style="padding:0 16px 6px 16px;">
          <div style="font-size:18px;font-weight:bold;color:{_DARK};margin-bottom:4px;">Boletos electrónicos</div>
          <div style="font-size:12px;color:#777;margin-bottom:14px;">Conserva este documento y preséntalo en el aeropuerto junto con tu identificación.</div>
          {banner}
          {''.join(bloques)}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def generar_boletos_pdf(reserva):
    """Genera el PDF de boletos estilo aerolínea. Devuelve bytes o None."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return None
    html = render_boletos_html(reserva, modo="pdf")
    buffer = io.BytesIO()
    try:
        result = pisa.CreatePDF(
            src=html, dest=buffer, encoding="utf-8", link_callback=_link_callback
        )
    except Exception:
        return None
    if result.err:
        return None
    return buffer.getvalue()

def _destinatarios_reserva(reserva):
    booking = reserva.get("booking") or {}
    correos = []
    contacto = (booking.get("contactInfo") or {}).get("emails") or []
    for c in contacto:
        if c and c not in correos:
            correos.append(c)
    for t in booking.get("travelers") or []:
        for e in t.get("emails") or []:
            if e and e not in correos:
                correos.append(e)
    pago = reserva.get("pago") or {}
    if pago.get("email") and pago["email"] not in correos:
        correos.append(pago["email"])
    return correos


def enviar_correo_reserva(reserva, destinatarios=None):
    """Envía el correo de confirmación con el voucher HTML + PDF adjunto.

    Returns: dict {'success': bool, 'message': str, 'destinatarios': [...]}
    """
    from .notifications import enviar_correo_html

    if destinatarios is None:
        destinatarios = _destinatarios_reserva(reserva)
    if not destinatarios:
        return {"success": False, "message": "Sin destinatarios", "destinatarios": []}

    ctx = _contexto(reserva)
    asunto = f"CorpoDG — Reserva {ctx['pnr']} confirmada y boletos emitidos"

    rutas = ", ".join(
        f"{v['numero']} {v['origen_codigo']}->{v['destino_codigo']} "
        f"{v['fecha_salida']} {v['hora_salida']}"
        for v in ctx["vuelos"]
    )
    mensaje_texto = (
        f"Reserva CONFIRMADA\n"
        f"PNR: {ctx['pnr']}\n"
        f"Ruta: {ctx['ruta']}\n"
        f"Pasajeros: {', '.join(ctx['pasajeros'])}\n"
        f"Vuelos: {rutas}\n"
        f"Total: {ctx['moneda']} {float(ctx['total']):.2f}\n"
        f"Adjuntamos tu voucher y tus boletos electrónicos en PDF.\n"
    )

    mensaje_html = render_voucher_html(reserva, modo="email")

    adjuntos = []
    pdf_bytes = generar_voucher_pdf(reserva)
    if pdf_bytes:
        adjuntos.append((f"CorpoDG_{ctx['pnr']}.pdf", pdf_bytes, "application/pdf"))

    # Boletos estilo aerolínea (PDF aparte)
    aerolinea = ""
    if ctx["vuelos"]:
        aerolinea = ctx["vuelos"][0].get("aerolinea_codigo") or ""
    boletos_pdf = generar_boletos_pdf(reserva)
    if boletos_pdf:
        nombre_bol = f"Boletos_{aerolinea + '_' if aerolinea else ''}{ctx['pnr']}.pdf"
        adjuntos.append((nombre_bol, boletos_pdf, "application/pdf"))

    resultado = enviar_correo_html(
        destinatarios=destinatarios,
        asunto=asunto,
        mensaje_texto=mensaje_texto,
        mensaje_html=mensaje_html,
        adjuntar_logo=True,
        adjuntos=adjuntos,
    )
    resultado["destinatarios"] = destinatarios
    return resultado
