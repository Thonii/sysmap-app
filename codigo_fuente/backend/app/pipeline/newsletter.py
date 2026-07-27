import logging
import httpx
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.config import RESEND_API_KEY, DEFAULT_CITY
from app.models.event import Event, Subscription

logger = logging.getLogger(__name__)

# Remitente verificado
EMAIL_FROM = "no-reply@tecnoancon.com"
RESEND_API_URL = "https://api.resend.com/emails"

def get_weekly_events(db: Session) -> list[Event]:
    """
    Obtiene los eventos tecnológicos en Buenos Aires para la próxima semana
    (desde el momento actual hasta 7 días en el futuro).
    """
    ahora = datetime.now(timezone.utc)
    una_semana_despues = ahora + timedelta(days=7)
    
    # Filtrar eventos futuros dentro del rango de 7 días
    events = db.query(Event).filter(
        Event.city == DEFAULT_CITY,
        Event.is_tech == True,
        Event.start_time >= ahora,
        Event.start_time <= una_semana_despues
    ).order_by(Event.start_time.asc()).all()
    
    return events

def build_newsletter_html(events: list[Event], subscriber_email: str) -> str:
    """
    Genera el HTML del boletín semanal con un diseño Solarpunk oscuro y premium,
    tarjetas de eventos responsivas, tags y CTAs.
    """
    # Enlace de desuscripción
    unsubscribe_url = f"https://sysmap.tecnoancon.com/api/subscriptions/unsubscribe?email={subscriber_email}"
    
    events_html = ""
    if not events:
        events_html = """
        <div style="text-align: center; padding: 30px; border: 1px dashed #334155; border-radius: 8px; background-color: #0f172a;">
            <p style="color: #94a3b8; font-size: 15px; margin: 0;">No hay eventos tecnológicos programados para esta semana.</p>
            <p style="color: #64748b; font-size: 13px; margin: 8px 0 0 0;">¡Estaremos listos para la próxima! Sigue atento a las novedades.</p>
        </div>
        """
    else:
        for ev in events:
            # Formatear fecha para el email
            start_local = ev.start_time.strftime("%A, %d de %B - %H:%M hs")
            # Traducir días de la semana a español simple
            traducciones = {
                "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo",
                "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
                "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
                "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
            }
            for eng, esp in traducciones.items():
                start_local = start_local.replace(eng, esp)
            
            # Badge de plataforma
            platform_color = "#3b82f6"  # Blue (Luma)
            if ev.source_platform.lower() == "meetup":
                platform_color = "#ef4444"  # Red
            elif ev.source_platform.lower() == "eventbrite":
                platform_color = "#f97316"  # Orange

            # Tags HTML
            tags_html = ""
            if ev.tags:
                for tag in ev.tags[:4]:
                    tags_html += f'<span style="display: inline-block; font-size: 11px; padding: 2px 6px; margin-right: 4px; margin-bottom: 4px; border-radius: 4px; background-color: #1e293b; color: #94a3b8; border: 1px solid #334155;">#{tag}</span>'

            # Google Maps Link
            query_map = ev.address or ev.venue_name or "Buenos Aires, Argentina"
            gmaps_url = f"https://www.google.com/maps/search/?api=1&query={query_map.replace(' ', '+')}"

            events_html += f"""
            <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 10px; font-weight: bold; color: {platform_color}; text-transform: uppercase; letter-spacing: 1px; background-color: rgba(255,255,255,0.03); border: 1px solid {platform_color}4D; padding: 2px 8px; border-radius: 12px;">
                        {ev.source_platform}
                    </span>
                </div>
                <h3 style="color: #ffffff; font-size: 17px; margin: 0 0 10px 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">{ev.title}</h3>
                
                <div style="font-size: 13px; color: #94a3b8; margin-bottom: 14px;">
                    <p style="margin: 4px 0;">📅 <strong>{start_local}</strong></p>
                    <p style="margin: 4px 0;">📍 <em>{ev.venue_name or ev.address or 'Online / A confirmar'}</em></p>
                </div>
                
                <div style="margin-bottom: 18px;">
                    {tags_html}
                </div>

                <div style="display: flex; gap: 10px;">
                    <a href="{gmaps_url}" target="_blank" style="flex: 1; text-align: center; background-color: #1e293b; border: 1px solid #334155; color: #ffffff; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; text-decoration: none; display: inline-block;">
                        📍 Cómo llegar
                    </a>
                    <a href="{ev.source_url}" target="_blank" style="flex: 1; text-align: center; background-color: #3b82f6; border: 1px solid #2563eb; color: #ffffff; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; text-decoration: none; display: inline-block; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);">
                        Registrarse
                    </a>
                </div>
            </div>
            """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agenda Semanal Tech - Sysmap</title>
    </head>
    <body style="background-color: #020617; color: #f8fafc; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 0; padding: 0;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #020617; margin: 0 auto; padding: 20px 10px;">
            <tr>
                <td style="text-align: center; padding: 20px 0 10px 0; border-bottom: 1px solid #1e293b;">
                    <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0; letter-spacing: -0.5px;">SYSMAP</h1>
                    <p style="color: #3b82f6; font-size: 11px; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; margin: 5px 0 0 0;">Buenos Aires Tech</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 30px 10px 10px 10px;">
                    <h2 style="color: #ffffff; font-size: 20px; font-weight: 700; margin-top: 0;">¡Tu Agenda Semanal de Tecnología ya está aquí! 🚀</h2>
                    <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                        Te traemos una selección curada de los próximos eventos tecnológicos, meetups y workshops en la zona de Buenos Aires para esta semana. ¡No te pierdas de conectar con la comunidad local!
                    </p>
                    
                    {events_html}
                </td>
            </tr>
            <tr>
                <td style="text-align: center; padding: 30px 10px 10px 10px; border-top: 1px solid #1e293b; color: #64748b; font-size: 11px;">
                    <p style="margin: 0 0 8px 0;">Este correo fue enviado de forma automática por Sysmap (TecnoAncon).</p>
                    <p style="margin: 0;">
                        ¿Ya no deseas recibir el boletín? 
                        <a href="{unsubscribe_url}" target="_blank" style="color: #3b82f6; text-decoration: underline;">Desuscribirse aquí</a>.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def build_welcome_html(subscriber_email: str, recent_events: list[Event]) -> str:
    """
    Genera el HTML de bienvenida interactivo al suscribirse por primera vez.
    """
    unsubscribe_url = f"https://sysmap.tecnoancon.com/api/subscriptions/unsubscribe?email={subscriber_email}"
    
    events_section = ""
    if recent_events:
        events_section += '<h3 style="color: #ffffff; font-size: 15px; margin: 20px 0 10px 0;">Aquí tienes algunos eventos destacados para empezar:</h3>'
        for ev in recent_events[:3]:
            start_local = ev.start_time.strftime("%d/%m %H:%M hs")
            events_section += f"""
            <div style="background-color: #0f172a; border-left: 3px solid #3b82f6; padding: 10px 15px; margin-bottom: 10px; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-size: 13px; font-weight: bold; color: #ffffff;">{ev.title}</p>
                <p style="margin: 4px 0 0 0; font-size: 11px; color: #94a3b8;">📅 {start_local} | 📍 {ev.venue_name or 'A confirmar'}</p>
            </div>
            """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bienvenido a Sysmap</title>
    </head>
    <body style="background-color: #020617; color: #f8fafc; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 0; padding: 0;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #020617; margin: 0 auto; padding: 20px 10px;">
            <tr>
                <td style="text-align: center; padding: 20px 0 10px 0; border-bottom: 1px solid #1e293b;">
                    <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0; letter-spacing: -0.5px;">SYSMAP</h1>
                    <p style="color: #3b82f6; font-size: 11px; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; margin: 5px 0 0 0;">Buenos Aires Tech</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 30px 10px 10px 10px;">
                    <h2 style="color: #ffffff; font-size: 20px; font-weight: 700; margin-top: 0; text-align: center;">¡Suscripción Confirmada! 🎉</h2>
                    <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 20px;">
                        Te has suscrito con éxito a <strong>Sysmap Buenos Aires Tech</strong>. A partir de ahora, todos los <strong>lunes a las 08:00 AM</strong> recibirás un boletín con la agenda semanal de eventos, workshops y meetups tecnológicos locales directamente en tu buzón.
                    </p>
                    
                    {events_section}
                    
                    <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-top: 25px;">
                        Si preferís cambiar tu canal de comunicación o verificar tus preferencias, recordá que siempre podés hacerlo directamente desde nuestra aplicación web.
                    </p>
                </td>
            </tr>
            <tr>
                <td style="text-align: center; padding: 30px 10px 10px 10px; border-top: 1px solid #1e293b; color: #64748b; font-size: 11px;">
                    <p style="margin: 0 0 8px 0;">Este correo fue enviado de forma automática por Sysmap (TecnoAncon).</p>
                    <p style="margin: 0;">
                        ¿Ya no deseas recibir el boletín? 
                        <a href="{unsubscribe_url}" target="_blank" style="color: #3b82f6; text-decoration: underline;">Desuscribirse aquí</a>.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

async def send_email_via_resend(to_email: str, subject: str, html_content: str) -> bool:
    """
    Envía un correo electrónico de forma asíncrona utilizando la API REST de Resend.
    Si no está configurada RESEND_API_KEY, simula el envío e imprime los logs para desarrollo local.
    """
    if not RESEND_API_KEY:
        logger.warning(
            f"[DESARROLLO LOCAL] RESEND_API_KEY no configurada. Simulando envío de email:\n"
            f"  - De: {EMAIL_FROM}\n"
            f"  - Para: {to_email}\n"
            f"  - Asunto: {subject}\n"
            f"  - Contenido HTML: (Longitud: {len(html_content)} bytes)"
        )
        return True

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(RESEND_API_URL, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                logger.info(f"Email enviado con éxito a {to_email} (ID Resend: {response.json().get('id')})")
                return True
            else:
                logger.error(
                    f"Fallo al enviar correo por Resend a {to_email}. "
                    f"Código de estado: {response.status_code}. Respuesta: {response.text}"
                )
                return False
    except Exception as e:
        logger.error(f"Error de red al conectar con Resend para {to_email}: {e}")
        return False

async def send_welcome_email(email: str, db: Session) -> bool:
    """
    Dispara el envío del email transaccional de bienvenida al suscribirse.
    """
    recent_events = get_weekly_events(db)
    html_content = build_welcome_html(email, recent_events)
    subject = "¡Bienvenido a Sysmap Buenos Aires Tech! 🚀"
    return await send_email_via_resend(email, subject, html_content)

async def send_weekly_newsletter(db: Session) -> dict:
    """
    Recupera los eventos semanales, busca a todos los suscriptores activos
    con preferencia por email, y les envía el boletín.
    """
    logger.info("Iniciando envío de boletín semanal...")
    
    events = get_weekly_events(db)
    logger.info(f"Se encontraron {len(events)} eventos para el boletín de la semana.")
    
    subscribers = db.query(Subscription).filter(
        Subscription.is_active == True,
        Subscription.email.isnot(None),
        Subscription.email != ""
    ).all()
    
    total_subscribers = len(subscribers)
    logger.info(f"Enviando a {total_subscribers} suscriptores activos...")
    
    sent_count = 0
    fail_count = 0
    
    for sub in subscribers:
        html_content = build_newsletter_html(events, sub.email)
        subject = f"Agenda Semanal: {len(events)} Eventos Tech en Buenos Aires 🚀"
        
        success = await send_email_via_resend(sub.email, subject, html_content)
        if success:
            sent_count += 1
        else:
            fail_count += 1
            
    logger.info(
        f"Proceso de boletín finalizado. "
        f"Resultados: Enviados={sent_count}, Fallidos={fail_count}, Total={total_subscribers}"
    )
    
    return {
        "total": total_subscribers,
        "sent": sent_count,
        "failed": fail_count,
        "events_count": len(events)
    }
