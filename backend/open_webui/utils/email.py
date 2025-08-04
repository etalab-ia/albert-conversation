import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from open_webui.env import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    EMAIL_NOTIFICATIONS_ENABLED,
)

log = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.enabled = EMAIL_NOTIFICATIONS_ENABLED

    def send_account_validation_email(self, user_email: str, user_name: str) -> bool:
        """
        Send account validation email to user when their status changes from pending to user
        """
        if not self.enabled:
            log.info("Email notifications are disabled")
            return True

        try:
            subject = "Votre compte Albert IA a été validé"

            # Create HTML email template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Compte Assistant IA validé</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Bienvenue {user_name} !</h2>
                    
                    <p>Votre compte Assistant IA a été validé avec succès.</p>
                    
                    <p>Vous pouvez maintenant accéder à l'Assistant IA en cliquant sur le lien ci-dessous :</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://albert.numerique.gouv.fr/" 
                           style="background-color: #0066cc; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Accéder à l'Assistant IA
                        </a>
                    </div>
                    
                    <p>Si vous avez des questions ou rencontrez des problèmes, n'hésitez pas à nous contacter.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        Cet email a été envoyé automatiquement. Merci de ne pas répondre à cette adresse.
                    </p>
                    
                    <p style="font-size: 12px; color: #666;">
                        Vous pouvez rejoindre la communauté sur Tchap : https://tchap.gouv.fr/#/room/!gpLYRJyIwdkcHBGYeC:agent.dinum.tchap.gouv.fr
                    </p>
                </div>
            </body>
            </html>
            """

            # Create plain text version
            text_body = f"""
            Félicitations {user_name} !
            
            Votre compte à l'Assistant IA a été validé avec succès.
            
            Vous pouvez maintenant accéder à l'Assistant IA à l'adresse suivante :
            https://albert.numerique.gouv.fr/
            
            Si vous avez des questions ou rencontrez des problèmes, n'hésitez pas à nous contacter.
            
            Vous pouvez rejoindre la communauté sur Tchap : https://tchap.gouv.fr/#/room/!gpLYRJyIwdkcHBGYeC:agent.dinum.tchap.gouv.fr
            
            ---
            Cet email a été envoyé automatiquement. Merci de ne pas répondre à cette adresse.
            """

            return self._send_email(user_email, subject, text_body, html_body)

        except Exception as e:
            log.error(f"Failed to send account validation email to {user_email}: {str(e)}")
            return False

    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str = None) -> bool:
        """
        Send email using SMTP
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # Add text part
            text_part = MIMEText(text_body, "plain", "utf-8")
            msg.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, "html", "utf-8")
                msg.attach(html_part)

            # Connect to SMTP server and send email
            try:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                    print(f"Email sent successfully to {to_email}")
            except Exception as e:
                print(f"Failed to send email to {to_email}: {str(e)}")
                log.error(f"Failed to send email to {to_email}: {str(e)}")
                return False

            log.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            log.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()
