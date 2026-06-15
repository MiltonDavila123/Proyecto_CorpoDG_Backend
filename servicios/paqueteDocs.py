"""Voucher de PAQUETES turísticos (HTML / PDF) + envío por correo.

Espejo de ``bookingDocs.py`` pero para la reserva de un paquete
(``confirmar_reserva_paquete``). Genera:

  * ``render_voucher_paquete_html(reserva, modo=...)`` -> HTML autocontenido
        con la marca CorpoDG: imagen del paquete, destino, duración, qué
        incluye, viajeros, totales y datos del pago.
  * ``generar_voucher_paquete_pdf(reserva)``           -> bytes PDF.
  * ``enviar_correo_paquete(reserva, destinatarios)``  -> correo con el PDF
        adjunto.
"""

import io

# Reutilizamos helpers ya existentes del módulo de vuelos.
from .bookingDocs import (
    _GOLD,
    _DARK,
    _corpodg_logo_datauri,
    _link_callback,
)


# Se usa un check (&#10003;) en lugar de emoji: los emoji se ven como
# cuadros negros en el PDF (xhtml2pdf no tiene fuente con emoji).
_ICONOS_INCLUYE = {
    "vuelo": ("&#10003;", "Vuelo"),
    "hotel": ("&#10003;", "Hotel"),
    "alimentacion": ("&#10003;", "Alimentación"),
    "traslados": ("&#10003;", "Traslados"),
    "tours": ("&#10003;", "Tours"),
    "seguro": ("&#10003;", "Seguro"),
}


def _contexto(reserva):
    """Normaliza la reserva de paquete en un dict listo para la plantilla."""
    paquete = reserva.get("paquete") or {}
    totales = reserva.get("totales") or {}
    pago = reserva.get("pago") or {}
    incluye = paquete.get("incluye") or {}

    viajeros = []
    for v in (reserva.get("viajeros") or []):
        if isinstance(v, dict):
            viajeros.append(v.get("nombre") or "")
        else:
            viajeros.append(str(v))
    viajeros = [v for v in viajeros if v]

    incluye_lista = [
        (glyph, label)
        for clave, (glyph, label) in _ICONOS_INCLUYE.items()
        if incluye.get(clave)
    ]

    aero = paquete.get("aerolinea") or {}
    duracion = ""
    if paquete.get("duracion_dias") or paquete.get("duracion_noches"):
        duracion = (f"{paquete.get('duracion_dias', 0)} días / "
                    f"{paquete.get('duracion_noches', 0)} noches")

    return {
        "localizador": reserva.get("localizador") or "",
        "estado": reserva.get("estado") or "CONFIRMADA",
        "sandbox": bool(reserva.get("sandbox")),
        "titulo": paquete.get("titulo") or "Paquete turístico",
        "subtitulo": paquete.get("subtitulo") or "",
        "destino": paquete.get("destino") or "",
        "imagen_url": paquete.get("imagen_url") or "",
        "descripcion": paquete.get("descripcion_corta") or "",
        "duracion": duracion,
        "salidas": paquete.get("salidas") or "",
        "fecha_salidas_texto": paquete.get("fecha_salidas_texto") or "",
        "fecha_viaje": reserva.get("fecha_viaje") or "",
        "temperatura": paquete.get("temperatura") or "",
        "idioma": paquete.get("idioma") or "",
        "moneda_local": paquete.get("moneda_local") or "",
        "documentos": paquete.get("documentos_requeridos") or "",
        "lugares": paquete.get("lugares_destacados") or [],
        "incluye": incluye_lista,
        "aerolinea_nombre": aero.get("nombre") or aero.get("codigo") or "",
        "aerolinea_logo": aero.get("logo") or "",
        "viajeros": viajeros,
        "n_personas": int(reserva.get("n_personas") or len(viajeros) or 1),
        "moneda": totales.get("moneda") or reserva.get("moneda") or "USD",
        "precio_unitario": float(totales.get("precio_unitario")
                                 or reserva.get("precio_unitario") or 0),
        "total": float(totales.get("total") or 0),
        "contacto": reserva.get("contacto") or {},
        "pago": {
            "estado": pago.get("estado") or "paid",
            "monto": float(pago.get("monto") or totales.get("total") or 0),
            "moneda": pago.get("moneda") or totales.get("moneda") or "USD",
            "proveedor": pago.get("proveedor") or "stripe",
            "recibo_url": pago.get("recibo_url"),
        },
    }


def render_voucher_paquete_html(reserva, modo="web"):
    """HTML del voucher del paquete.

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
        if logo_src else
        '<span style="color:#fff;font-size:22px;font-weight:bold;">CorpoDG</span>'
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

    imagen_html = ""
    if ctx["imagen_url"]:
        imagen_html = (
            f'<tr><td style="background:#fff;padding:0 24px;">'
            f'<img src="{ctx["imagen_url"]}" alt="{ctx["titulo"]}" '
            f'style="width:100%;max-height:240px;border-radius:10px;" />'
            f"</td></tr>"
        )

    # Chips de "incluye"
    incluye_html = ""
    for glyph, label in ctx["incluye"]:
        incluye_html += (
            f'<span style="display:inline-block;background:#f3f1ff;color:{_DARK};'
            f'border:1px solid #e0dcff;border-radius:16px;padding:6px 12px;'
            f'margin:0 6px 8px 0;font-size:12px;font-weight:bold;">'
            f'{glyph} {label}</span>'
        )
    if not incluye_html:
        incluye_html = '<span style="color:#888;font-size:13px;">—</span>'

    # Lugares destacados
    lugares_html = ""
    if ctx["lugares"]:
        items = "".join(
            f'<li style="padding:2px 0;color:#444;">{lug}</li>'
            for lug in ctx["lugares"]
        )
        lugares_html = (
            f'<div style="font-size:14px;font-weight:bold;color:{_DARK};'
            f'margin:14px 0 6px 0;">Lugares destacados</div>'
            f'<ul style="margin:0;padding-left:18px;font-size:13px;">{items}</ul>'
        )

    # Detalles laterales (temperatura, idioma, etc.)
    detalles = []
    if ctx["fecha_viaje"]:
        detalles.append(("Fecha de viaje", ctx["fecha_viaje"]))
    elif ctx["fecha_salidas_texto"]:
        detalles.append(("Salidas", ctx["fecha_salidas_texto"]))
    if ctx["salidas"]:
        detalles.append(("Punto de salida", ctx["salidas"]))
    if ctx["temperatura"]:
        detalles.append(("Temperatura", ctx["temperatura"]))
    if ctx["idioma"]:
        detalles.append(("Idioma", ctx["idioma"]))
    if ctx["moneda_local"]:
        detalles.append(("Moneda local", ctx["moneda_local"]))
    if ctx["aerolinea_nombre"]:
        detalles.append(("Aerolínea", ctx["aerolinea_nombre"]))
    if ctx["documentos"]:
        detalles.append(("Documentos requeridos", ctx["documentos"]))

    detalles_html = "".join(
        f'<tr><td style="padding:5px 0;color:#888;font-size:12px;width:42%;">{k}</td>'
        f'<td style="padding:5px 0;color:#333;font-size:13px;font-weight:bold;">{v}</td></tr>'
        for k, v in detalles
    )

    # Viajeros (se usa un check en vez de emoji por compatibilidad con el PDF)
    filas_viajeros = "".join(
        f'<tr><td style="padding:6px 0;color:#333;">'
        f'<span style="color:{_GOLD};font-weight:bold;">&#10003;</span> {nombre}</td></tr>'
        for nombre in ctx["viajeros"]
    )

    recibo_link = ""
    if ctx["pago"]["recibo_url"]:
        recibo_link = (
            f'<div style="margin-top:8px;"><a href="{ctx["pago"]["recibo_url"]}" '
            f'style="color:{_GOLD};font-size:12px;">Ver recibo de pago</a></div>'
        )

    # Contenedor: full-width en PDF, centrado fijo en web/email.
    if modo == "pdf":
        wrap_open = ('<table width="100%" cellpadding="0" cellspacing="0" '
                     'style="width:100%;">')
        wrap_close = "</table>"
    else:
        wrap_open = ('<table width="100%" cellpadding="0" cellspacing="0" '
                     'style="background:#eef0f5;padding:24px 0;">'
                     '<tr><td align="center">'
                     '<table width="640" cellpadding="0" cellspacing="0" '
                     'style="max-width:640px;">')
        wrap_close = "</table></td></tr></table>"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>Reserva {ctx['localizador']} - CorpoDG</title>
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
          <div style="color:#fff;font-size:13px;margin-top:6px;">Confirmación de reserva de paquete</div>
        </td></tr>

        <!-- Estado -->
        <tr><td style="background:#fff;padding:26px 24px 6px 24px;text-align:center;">
          <div style="width:56px;height:56px;line-height:56px;border-radius:50%;background:#16a34a;color:#fff;font-size:28px;margin:0 auto 10px auto;">&#10003;</div>
          <div style="font-size:22px;font-weight:bold;color:{_DARK};">¡Reserva confirmada!</div>
          <div style="color:#667;font-size:14px;margin-top:4px;">Tu paquete turístico fue reservado correctamente.</div>
        </td></tr>

        <tr><td style="background:#fff;padding:10px 24px 0 24px;">{banner_sandbox}</td></tr>

        <!-- Localizador + Pago -->
        <tr><td style="background:#fff;padding:0 24px 18px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="50%" valign="top" style="padding-right:8px;">
                <table width="100%" style="background:{_DARK};border-radius:10px;">
                  <tr><td style="padding:18px;text-align:center;">
                    <div style="color:#b9b6d6;font-size:12px;">Código de reserva</div>
                    <div style="color:#fff;font-size:26px;font-weight:bold;letter-spacing:2px;">{ctx['localizador']}</div>
                    <div style="color:#cfcce6;font-size:13px;margin-top:4px;">{ctx['destino']}</div>
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
                      <tr><td style="padding:3px 0;">Monto</td><td align="right" style="font-weight:bold;">{ctx['pago']['moneda']} {ctx['pago']['monto']:.2f}</td></tr>
                      <tr><td style="padding:3px 0;">Proveedor</td><td align="right" style="font-weight:bold;">{ctx['pago']['proveedor']}</td></tr>
                    </table>
                    {recibo_link}
                  </td></tr>
                </table>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Título del paquete -->
        <tr><td style="background:#fff;padding:6px 24px 8px 24px;">
          <div style="font-size:20px;font-weight:bold;color:{_DARK};">{ctx['titulo']}</div>
          <div style="font-size:13px;color:#888;">{ctx['subtitulo']}</div>
          <div style="font-size:13px;color:#555;margin-top:6px;">{ctx['descripcion']}</div>
          <div style="margin-top:8px;">
            <span style="display:inline-block;background:{_GOLD};color:#fff;font-size:12px;font-weight:bold;padding:5px 14px;border-radius:14px;">{ctx['destino']}</span>
            <span style="display:inline-block;background:#1f1a3d;color:#fff;font-size:12px;font-weight:bold;padding:5px 14px;border-radius:14px;margin-left:6px;">{ctx['duracion']}</span>
          </div>
        </td></tr>

        {imagen_html}

        <!-- Incluye -->
        <tr><td style="background:#fff;padding:16px 24px 0 24px;">
          <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:10px;">El paquete incluye</div>
          {incluye_html}
        </td></tr>

        <!-- Detalles + Lugares -->
        <tr><td style="background:#fff;padding:14px 24px 0 24px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="55%" valign="top" style="padding-right:10px;">
                <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:8px;">Detalles del viaje</div>
                <table width="100%">{detalles_html}</table>
              </td>
              <td width="45%" valign="top" style="padding-left:10px;">
                {lugares_html}
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Totales + Viajeros -->
        <tr><td style="background:#fff;padding:18px 24px 24px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="55%" valign="top" style="padding-right:8px;">
                <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:10px;">Totales</div>
                <table width="100%" style="font-size:14px;">
                  <tr><td style="padding:6px 0;color:#555;">Precio por persona</td><td align="right" style="padding:6px 0;color:#333;font-weight:bold;">{ctx['moneda']} {ctx['precio_unitario']:.2f}</td></tr>
                  <tr><td style="padding:6px 0;color:#555;">Personas</td><td align="right" style="padding:6px 0;color:#333;font-weight:bold;">{ctx['n_personas']}</td></tr>
                  <tr><td style="padding:10px 0;border-top:2px solid #222;font-weight:bold;color:{_DARK};">Total</td>
                      <td align="right" style="padding:10px 0;border-top:2px solid #222;font-weight:bold;font-size:16px;color:{_DARK};">{ctx['moneda']} {ctx['total']:.2f}</td></tr>
                </table>
              </td>
              <td width="45%" valign="top" style="padding-left:8px;">
                <div style="font-size:16px;font-weight:bold;color:{_DARK};margin-bottom:10px;">Viajeros</div>
                <table width="100%" style="font-size:14px;">{filas_viajeros}</table>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:{_DARK};border-radius:0 0 12px 12px;padding:18px;text-align:center;">
          <div style="color:#fff;font-size:12px;">© 2026 CorpoDG — Todos los derechos reservados</div>
          <div style="color:#b9b6d6;font-size:11px;margin-top:4px;">Este documento es tu comprobante de reserva. Nuestro equipo te contactará con los detalles finales del viaje.</div>
        </td></tr>

      {wrap_close}
</body>
</html>"""


def generar_voucher_paquete_pdf(reserva):
    """Genera el PDF del voucher del paquete. Devuelve bytes o None."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return None
    html = render_voucher_paquete_html(reserva, modo="pdf")
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
    correos = []
    contacto = reserva.get("contacto") or {}
    if contacto.get("email"):
        correos.append(contacto["email"])
    pago = reserva.get("pago") or {}
    if pago.get("email") and pago["email"] not in correos:
        correos.append(pago["email"])
    return correos


def enviar_correo_paquete(reserva, destinatarios=None):
    """Envía el voucher del paquete por correo con el PDF adjunto.

    Returns: dict {'success': bool, 'message': str, 'destinatarios': [...]}
    """
    from .notifications import enviar_correo_html

    if destinatarios is None:
        destinatarios = _destinatarios_reserva(reserva)
    if not destinatarios:
        return {"success": False, "message": "Sin destinatarios", "destinatarios": []}

    ctx = _contexto(reserva)
    asunto = f"CorpoDG — Reserva {ctx['localizador']} confirmada: {ctx['titulo']}"

    mensaje_texto = (
        f"Reserva CONFIRMADA\n"
        f"Código: {ctx['localizador']}\n"
        f"Paquete: {ctx['titulo']}\n"
        f"Destino: {ctx['destino']}\n"
        f"Duración: {ctx['duracion']}\n"
        f"Personas: {ctx['n_personas']}\n"
        f"Total: {ctx['moneda']} {ctx['total']:.2f}\n"
        f"Adjuntamos tu voucher en PDF.\n"
    )

    mensaje_html = render_voucher_paquete_html(reserva, modo="email")

    adjuntos = []
    pdf_bytes = generar_voucher_paquete_pdf(reserva)
    if pdf_bytes:
        adjuntos.append((f"CorpoDG_Paquete_{ctx['localizador']}.pdf",
                         pdf_bytes, "application/pdf"))

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
