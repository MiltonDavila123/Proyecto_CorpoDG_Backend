"""
Módulo de notificaciones desacoplado.
Contiene funciones reutilizables para enviar correos y mensajes de WhatsApp.
"""
import os
import requests
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage


# =============================================================================
# FUNCIONES DE WHATSAPP
# =============================================================================

def enviar_whatsapp_plantilla(numero_destino, nombre_plantilla, idioma, parametros):
    """
    Envía un mensaje de WhatsApp usando una plantilla de Meta Business.
    
    Args:
        numero_destino (str): Número de teléfono destino (formato: 593959807049)
        nombre_plantilla (str): Nombre de la plantilla en Meta Business
        idioma (str): Código de idioma (ej: 'es_EC', 'en_US')
        parametros (list): Lista de strings con los valores de las variables {{1}}, {{2}}, etc.
    
    Returns:
        dict: {'success': bool, 'message': str, 'response': dict|None}
    
    Ejemplo:
        enviar_whatsapp_plantilla(
            numero_destino='593959807049',
            nombre_plantilla='plantilla_contacto',
            idioma='es_EC',
            parametros=['Juan Pérez', 'juan@email.com', '0991234567', 'Mensaje del cliente']
        )
    """
    try:
        # Verificar credenciales
        if not settings.WHATSAPP_TOKEN:
            print("WhatsApp Error: WHATSAPP_TOKEN no está configurado en .env")
            return {
                'success': False,
                'message': 'WHATSAPP_TOKEN no configurado',
                'response': None
            }
        
        if not settings.WHATSAPP_PHONE_NUMBER_ID:
            print("WhatsApp Error: WHATSAPP_PHONE_NUMBER_ID no está configurado en .env")
            return {
                'success': False,
                'message': 'WHATSAPP_PHONE_NUMBER_ID no configurado',
                'response': None
            }
        
        if not numero_destino:
            print("WhatsApp Error: Número destino vacío")
            return {
                'success': False,
                'message': 'Número destino no configurado',
                'response': None
            }
        
        url = f"https://graph.facebook.com/v22.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Construir los parámetros del body
        body_parameters = [
            {"type": "text", "text": str(param)[:1024]} for param in parametros
        ]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": numero_destino,
            "type": "template",
            "template": {
                "name": nombre_plantilla,
                "language": {"code": idioma},
                "components": [
                    {
                        "type": "body",
                        "parameters": body_parameters
                    }
                ]
            }
        }
        
        # Debug: mostrar qué se está enviando
        print("=" * 50)
        print("📱 ENVIANDO WHATSAPP:")
        print(f"   URL: {url}")
        print(f"   Destino: {numero_destino}")
        print(f"   Plantilla: {nombre_plantilla}")
        print(f"   Idioma: {idioma}")
        print(f"   Parámetros: {parametros}")
        print("=" * 50)
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Respuesta Status: {response.status_code}")
        print(f"Respuesta Body: {response.text}")
        
        if response.status_code == 200:
            print("WhatsApp: Mensaje enviado exitosamente!")
            return {
                'success': True,
                'message': 'Mensaje enviado exitosamente',
                'response': response.json()
            }
        else:
            print(f"WhatsApp Error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'message': f'Error {response.status_code}: {response.text}',
                'response': response.json() if response.text else None
            }
            
    except Exception as e:
        print(f"WhatsApp Exception: {str(e)}")
        return {
            'success': False,
            'message': f'Excepción: {str(e)}',
            'response': None
        }


def enviar_whatsapp_contacto(cliente_nombre, cliente_email, cliente_telefono, mensaje):
    """
    Función específica para enviar notificación de contacto por WhatsApp.
    Usa la plantilla y configuración por defecto del .env
    
    Args:
        cliente_nombre (str): Nombre completo del cliente
        cliente_email (str): Email del cliente
        cliente_telefono (str): Teléfono del cliente
        mensaje (str): Mensaje del cliente
    
    Returns:
        dict: {'success': bool, 'message': str, 'response': dict|None}
    """
    return enviar_whatsapp_plantilla(
        numero_destino=settings.WHATSAPP_RECIPIENT_NUMBER,
        nombre_plantilla=settings.WHATSAPP_TEMPLATE_NAME,
        idioma=settings.WHATSAPP_TEMPLATE_LANGUAGE,
        parametros=[cliente_nombre, cliente_email, cliente_telefono, mensaje]
    )


# =============================================================================
# FUNCIONES DE CORREO ELECTRÓNICO
# =============================================================================

# Fallback si aún no existe la configuración en la BD
_DESTINATARIOS_FALLBACK = ['miltondaviladt@gmail.com', 'milton.davila.torres@udla.edu.ec']


def obtener_config_notificaciones():
    """Retorna la configuración de notificaciones o None si no está disponible."""
    try:
        from .models import ConfiguracionNotificaciones
        return ConfiguracionNotificaciones.load()
    except Exception:  # noqa: BLE001 (BD no migrada, etc.)
        return None


def obtener_destinatarios_notificacion():
    """Correos configurados en el admin para recibir notificaciones."""
    config = obtener_config_notificaciones()
    if config:
        destinatarios = config.get_destinatarios()
        if destinatarios:
            return destinatarios
    return list(_DESTINATARIOS_FALLBACK)

def enviar_correo_html(destinatarios, asunto, mensaje_texto, mensaje_html, 
                       from_email=None, adjuntar_logo=True, adjuntos=None):
    """
    Envía un correo electrónico con versión HTML y texto plano.
    
    Args:
        destinatarios (list): Lista de emails destino
        asunto (str): Asunto del correo
        mensaje_texto (str): Versión en texto plano del mensaje
        mensaje_html (str): Versión HTML del mensaje
        from_email (str, optional): Email remitente. Default: settings.EMAIL_HOST_USER
        adjuntar_logo (bool): Si adjuntar el logo de la empresa
        adjuntos (list, optional): Lista de adjuntos como tuplas
            (nombre_archivo, contenido_bytes, mimetype). Ej:
            [("voucher.pdf", b"...", "application/pdf")]
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        if from_email is None:
            from_email = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL
        
        if isinstance(destinatarios, str):
            destinatarios = [destinatarios]
        
        email = EmailMultiAlternatives(
            subject=asunto,
            body=mensaje_texto,
            from_email=from_email,
            to=destinatarios
        )
        
        email.attach_alternative(mensaje_html, "text/html")
        
        # Adjuntar logo si se solicita
        if adjuntar_logo:
            logo_path = os.path.join(settings.BASE_DIR, 'servicios', 'static', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as img:
                    logo_img = MIMEImage(img.read())
                    logo_img.add_header('Content-ID', '<logo_corpodg>')
                    logo_img.add_header('Content-Disposition', 'inline', filename='logo.png')
                    email.attach(logo_img)
        
        # Adjuntos arbitrarios (ej: voucher PDF)
        if adjuntos:
            for adj in adjuntos:
                try:
                    nombre, contenido, mimetype = adj
                    if contenido:
                        email.attach(nombre, contenido, mimetype)
                except (ValueError, TypeError):
                    continue
        
        email.send(fail_silently=False)
        
        return {
            'success': True,
            'message': 'Correo enviado exitosamente'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error enviando correo: {str(e)}'
        }


def enviar_correo_contacto(cliente_nombre, cliente_email, cliente_telefono, mensaje,
                            destinatarios=None):
    """
    Función específica para enviar notificación de contacto por correo.
    
    Args:
        cliente_nombre (str): Nombre completo del cliente
        cliente_email (str): Email del cliente
        cliente_telefono (str): Teléfono del cliente
        mensaje (str): Mensaje del cliente
        destinatarios (list, optional): Lista de emails. Default: los correos
            configurados en el admin (Configuración de Notificaciones).

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if destinatarios is None:
        config = obtener_config_notificaciones()
        if config and not config.notificar_contacto:
            return {'success': False,
                    'message': 'Notificaciones de contacto desactivadas en el admin'}
        destinatarios = obtener_destinatarios_notificacion()
    
    mensaje_texto = f"""
NUEVO CONTACTO:

NOMBRE: {cliente_nombre}
EMAIL: {cliente_email}
TELÉFONO: {cliente_telefono}

MENSAJE:
{mensaje}
"""
    
    mensaje_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        
        <!-- Header con logo -->
        <div style="background-color: #B8860B; padding: 20px; text-align: center;">
            <img src="cid:logo_corpodg" alt="CORPODG Logo" style="max-width: 200px; height: auto; margin-bottom: 10px;" />
            <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 14px;">Nuevo contacto desde la web</p>
        </div>
        
        <!-- Contenido -->
        <div style="padding: 30px;">
            <h2 style="color: #333; border-bottom: 2px solid #B8860B; padding-bottom: 10px;">Datos del Cliente</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; background-color: #f9f9f9; font-weight: bold; width: 30%;">Nombre:</td>
                    <td style="padding: 10px; background-color: #f9f9f9;">{cliente_nombre}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Email:</td>
                    <td style="padding: 10px;"><a href="mailto:{cliente_email}" style="color: #B8860B;">{cliente_email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 10px; background-color: #f9f9f9; font-weight: bold;">Teléfono:</td>
                    <td style="padding: 10px; background-color: #f9f9f9;"><a href="https://wa.me/593{cliente_telefono}" target="_blank" style="color: #B8860B;">{cliente_telefono}</a></td>
                </tr>
            </table>
            
            <h2 style="color: #333; border-bottom: 2px solid #B8860B; padding-bottom: 10px;">Mensaje</h2>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #B8860B;">
                <p style="margin: 0; line-height: 1.6; color: #555;">{mensaje}</p>
            </div>
        </div>
        
        <div style="background-color: #333; padding: 20px; text-align: center;">
            <p style="color: #ffffff; margin: 0; font-size: 12px;">© 2026 CorpoDG - Todos los derechos reservados</p>
            <p style="color: #B8860B; margin: 10px 0 0 0; font-size: 11px;">Este correo fue generado automáticamente desde el formulario de contacto</p>
        </div>
        
    </div>
</body>
</html>
"""
    
    return enviar_correo_html(
        destinatarios=destinatarios,
        asunto='CLIENTE QUIERE CONTACTARSE DESDE LA WEB',
        mensaje_texto=mensaje_texto,
        mensaje_html=mensaje_html,
        adjuntar_logo=True
    )


# =============================================================================
# FUNCIÓN COMBINADA
# =============================================================================

def notificar_contacto(cliente_nombre, cliente_email, cliente_telefono, mensaje,
                       enviar_email=True, enviar_whatsapp=True, destinatarios_email=None):
    """
    Función combinada para enviar notificaciones de contacto por múltiples canales.
    
    Args:
        cliente_nombre (str): Nombre completo del cliente
        cliente_email (str): Email del cliente
        cliente_telefono (str): Teléfono del cliente
        mensaje (str): Mensaje del cliente
        enviar_email (bool): Si enviar por correo. Default: True
        enviar_whatsapp (bool): Si enviar por WhatsApp. Default: True
        destinatarios_email (list, optional): Lista de emails destino
    
    Returns:
        dict: {
            'email': {'success': bool, 'message': str} or None,
            'whatsapp': {'success': bool, 'message': str} or None
        }
    """
    resultado = {
        'email': None,
        'whatsapp': None
    }
    
    if enviar_email:
        resultado['email'] = enviar_correo_contacto(
            cliente_nombre=cliente_nombre,
            cliente_email=cliente_email,
            cliente_telefono=cliente_telefono,
            mensaje=mensaje,
            destinatarios=destinatarios_email
        )
    
    if enviar_whatsapp:
        resultado['whatsapp'] = enviar_whatsapp_contacto(
            cliente_nombre=cliente_nombre,
            cliente_email=cliente_email,
            cliente_telefono=cliente_telefono,  
            mensaje=mensaje
        )
    
    return resultado


# =============================================================================
# NOTIFICACIÓN DE NUEVAS RESERVAS (al correo configurado en el admin)
# =============================================================================

def enviar_correo_nueva_reserva(tipo, codigo, email_cliente, telefono_cliente,
                                monto, moneda, detalle, detalle_extra=None):
    """
    Notifica al correo configurado en el admin que se confirmó una reserva.

    Args:
        tipo (str): 'vuelo' o 'paquete'
        codigo (str): PNR (vuelo) o localizador (paquete)
        email_cliente (str): Email del cliente
        telefono_cliente (str): Teléfono del cliente
        monto (float): Monto total pagado
        moneda (str): Moneda del pago
        detalle (str): Descripción corta (ruta del vuelo o título del paquete)
        detalle_extra (dict, optional): Pares extra {etiqueta: valor} para la tabla

    Returns:
        dict: {'success': bool, 'message': str}
    """
    config = obtener_config_notificaciones()
    if config and not config.notificar_reservas:
        return {'success': False,
                'message': 'Notificaciones de reservas desactivadas en el admin'}
    destinatarios = obtener_destinatarios_notificacion()

    tipo_display = 'VUELO' if tipo == 'vuelo' else 'PAQUETE'
    filas = {
        'Tipo de reserva': tipo_display,
        'Código': codigo,
        'Detalle': detalle,
        'Email del cliente': email_cliente or 'No indicado',
        'Teléfono del cliente': telefono_cliente or 'No indicado',
        'Monto pagado': f"{monto} {moneda}",
    }
    if detalle_extra:
        filas.update(detalle_extra)

    mensaje_texto = f"NUEVA RESERVA DE {tipo_display} CONFIRMADA:\n\n"
    mensaje_texto += "\n".join(f"{k}: {v}" for k, v in filas.items())
    mensaje_texto += ("\n\nRevisa el panel de administración para gestionarla "
                      "y enviarla a facturación.")

    filas_html = "".join(
        f'<tr>'
        f'<td style="padding: 10px; background-color: #f9f9f9; font-weight: bold; width: 35%;">{k}:</td>'
        f'<td style="padding: 10px;">{v}</td>'
        f'</tr>'
        for k, v in filas.items()
    )
    mensaje_html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background-color: #1a365d; padding: 20px; text-align: center;">
            <img src="cid:logo_corpodg" alt="CORPODG Logo" style="max-width: 200px; height: auto; margin-bottom: 10px;" />
            <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 16px; font-weight: bold;">
                Nueva reserva de {tipo_display} confirmada
            </p>
        </div>
        <div style="padding: 30px;">
            <h2 style="color: #333; border-bottom: 2px solid #1a365d; padding-bottom: 10px;">
                Reserva {codigo}
            </h2>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                {filas_html}
            </table>
            <p style="color: #555;">Ingresa al panel de administración
               (Reservas de {'Vuelos' if tipo == 'vuelo' else 'Paquetes'})
               para revisarla, gestionarla y enviarla a facturación.</p>
        </div>
        <div style="background-color: #333; padding: 20px; text-align: center;">
            <p style="color: #ffffff; margin: 0; font-size: 12px;">© 2026 CorpoDG - Todos los derechos reservados</p>
            <p style="color: #B8860B; margin: 10px 0 0 0; font-size: 11px;">Correo automático de notificación de reservas</p>
        </div>
    </div>
</body>
</html>
"""

    return enviar_correo_html(
        destinatarios=destinatarios,
        asunto=f'NUEVA RESERVA DE {tipo_display} - {codigo}',
        mensaje_texto=mensaje_texto,
        mensaje_html=mensaje_html,
        adjuntar_logo=True,
    )


def notificar_nueva_reserva_async(tipo, codigo, email_cliente, telefono_cliente,
                                  monto, moneda, detalle, detalle_extra=None):
    """Envía la notificación de nueva reserva en un hilo de fondo (best-effort)."""
    import threading

    def _worker():
        try:
            enviar_correo_nueva_reserva(tipo, codigo, email_cliente,
                                        telefono_cliente, monto, moneda,
                                        detalle, detalle_extra)
        except Exception:  # noqa: BLE001
            pass

    threading.Thread(target=_worker, daemon=True).start()
