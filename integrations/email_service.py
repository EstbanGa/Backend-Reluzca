"""
Email service for sending verification emails, notifications, etc.
Uses SMTP with Gmail credentials from environment variables.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""
    
    @staticmethod
    def send_verification_email(email: str, token: str, nombre: str) -> bool:
        """
        Envía un correo de verificación al usuario.
        
        Args:
            email: Correo del destinatario
            token: Token de verificación generado
            nombre: Nombre del usuario
            
        Returns:
            bool: True si se envió correctamente, False si hubo error
        """
        try:
            verify_url = f"{settings.FRONTEND_URL}/auth/email?token={token}"
            
            # HTML del correo (mismo diseño que Django)
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Confirma tu cuenta - Reluzca</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Spartan', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background-color: #FCF7F0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #4894AD 0%, #195083 100%); padding: 40px 30px; text-align: center;">
                        <h1 style="color: white; font-size: 32px; font-weight: 800; margin: 0; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                            Reluzca
                        </h1>
                        <p style="color: #F5F0E7; font-size: 16px; margin: 8px 0 0 0; opacity: 0.9;">
                            Servicios de limpieza profesional
                        </p>
                    </div>

                    <!-- Content -->
                    <div style="padding: 40px 30px;">
                        <h2 style="color: #195083; font-size: 24px; font-weight: 700; margin: 0 0 20px 0;">
                            ¡Hola, {nombre}!
                        </h2>
                        
                        <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                            Gracias por registrarte en <strong style="color: #4894AD;">Reluzca</strong>. 
                            Estamos emocionados de tenerte con nosotros.
                        </p>
                        
                        <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                            Para completar tu registro y activar tu cuenta, por favor haz clic en el botón de abajo:
                        </p>
                        
                        <!-- Button -->
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verify_url}" 
                               style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #4894AD 0%, #195083 100%); color: white; text-decoration: none; font-size: 16px; font-weight: 700; border-radius: 8px; box-shadow: 0 4px 12px rgba(72, 148, 173, 0.3); transition: transform 0.2s;">
                                Verificar mi correo
                            </a>
                        </div>
                        
                        <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 30px 0 10px 0;">
                            O copia y pega este enlace en tu navegador:
                        </p>
                        
                        <div style="background-color: #F5F0E7; padding: 15px; border-radius: 6px; word-break: break-all;">
                            <a href="{verify_url}" style="color: #4894AD; text-decoration: none; font-size: 14px;">
                                {verify_url}
                            </a>
                        </div>
                        
                        <p style="color: #999999; font-size: 13px; line-height: 1.6; margin: 25px 0 0 0; padding-top: 20px; border-top: 1px solid #eeeeee;">
                            <strong>Nota:</strong> Este enlace expirará en 48 horas por razones de seguridad.
                        </p>
                    </div>

                    <!-- Footer -->
                    <div style="background-color: #F5F0E7; padding: 30px; text-align: center;">
                        <p style="color: #666666; font-size: 14px; margin: 0 0 10px 0;">
                            ¿Necesitas ayuda? Contáctanos
                        </p>
                        <p style="color: #4894AD; font-size: 14px; font-weight: 600; margin: 0;">
                            {settings.DEFAULT_FROM_EMAIL}
                        </p>
                        <p style="color: #999999; font-size: 12px; margin: 20px 0 0 0;">
                            © 2024 Reluzca. Todos los derechos reservados.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = "Verifica tu cuenta en Reluzca"
            message["From"] = f"Reluzca <{settings.EMAIL_HOST_USER}>"
            message["To"] = email
            
            # Adjuntar HTML
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Enviar
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(message)
            
            logger.info(f"Email de verificación enviado a {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de verificación a {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_notification_email(
        email: str,
        subject: str,
        message: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Envía un correo de notificación genérico.
        
        Args:
            email: Correo del destinatario
            subject: Asunto del correo
            message: Mensaje de texto plano
            html_content: Contenido HTML opcional
            
        Returns:
            bool: True si se envió correctamente, False si hubo error
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Reluzca <{settings.EMAIL_HOST_USER}>"
            msg["To"] = email
            
            # Texto plano
            text_part = MIMEText(message, "plain")
            msg.attach(text_part)
            
            # HTML si se proporciona
            if html_content:
                html_part = MIMEText(html_content, "html")
                msg.attach(html_part)
            
            # Enviar
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email de notificación enviado a {email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de notificación a {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(email: str, token: str, nombre: str) -> bool:
        """
        Envía un correo para restablecer contraseña.
        
        Args:
            email: Correo del destinatario
            token: Token de restablecimiento
            nombre: Nombre del usuario
            
        Returns:
            bool: True si se envió correctamente, False si hubo error
        """
        try:
            reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Restablecer Contraseña - Reluzca</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Spartan', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background-color: #FCF7F0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    
                    <div style="background: linear-gradient(135deg, #4894AD 0%, #195083 100%); padding: 40px 30px; text-align: center;">
                        <h1 style="color: white; font-size: 32px; font-weight: 800; margin: 0;">Reluzca</h1>
                    </div>

                    <div style="padding: 40px 30px;">
                        <h2 style="color: #195083; font-size: 24px; font-weight: 700; margin: 0 0 20px 0;">
                            Hola, {nombre}
                        </h2>
                        
                        <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                            Recibimos una solicitud para restablecer la contraseña de tu cuenta.
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" 
                               style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #4894AD 0%, #195083 100%); color: white; text-decoration: none; font-size: 16px; font-weight: 700; border-radius: 8px;">
                                Restablecer contraseña
                            </a>
                        </div>
                        
                        <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 30px 0 10px 0;">
                            O copia y pega este enlace:
                        </p>
                        
                        <div style="background-color: #F5F0E7; padding: 15px; border-radius: 6px; word-break: break-all;">
                            <a href="{reset_url}" style="color: #4894AD; text-decoration: none; font-size: 14px;">
                                {reset_url}
                            </a>
                        </div>
                        
                        <p style="color: #999999; font-size: 13px; line-height: 1.6; margin: 25px 0 0 0;">
                            Si no solicitaste restablecer tu contraseña, ignora este correo.
                        </p>
                    </div>

                    <div style="background-color: #F5F0E7; padding: 30px; text-align: center;">
                        <p style="color: #999999; font-size: 12px; margin: 0;">
                            © 2024 Reluzca. Todos los derechos reservados.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Restablecer contraseña - Reluzca"
            message["From"] = f"Reluzca <{settings.EMAIL_HOST_USER}>"
            message["To"] = email
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(message)
            
            logger.info(f"Email de restablecimiento enviado a {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de restablecimiento a {email}: {str(e)}")
            return False
