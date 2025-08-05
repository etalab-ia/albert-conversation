import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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
            subject = "Votre compte Assistant IA a été créé"

            # Create HTML email template
            html_body = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Votre compte Assistant IA a été créé</title>
                <style>
                    body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #FFFFFF; }
                    .container { max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border: 1px solid #E5E7EB; }
                    .header { background-color: #000091; height: 8px; }
                    .header-accent { background-color: #E1000F; height: 3px; }
                    .content { padding: 40px 30px; background-color: #FFFFFF; }
                    .logo-section { text-align: center; margin-bottom: 30px; }
                    .logo-text { color: #000091; font-size: 26px; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
                    .subtitle { color: #000091; font-size: 14px; margin: 5px 0 0 0; font-weight: 500; }
                    .btn-primary { background-color: #000091; color: #FFFFFF; padding: 16px 32px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: 700; letter-spacing: 0.3px; box-shadow: 0 2px 8px rgba(0,0,145,0.15); }
                    .btn-secondary { background-color: #E1000F; color: #FFFFFF; padding: 14px 28px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: 700; letter-spacing: 0.3px; box-shadow: 0 2px 8px rgba(225,0,15,0.15); }
                    .btn-container { text-align: center; margin: 30px 0; }
                    .footer { background-color: #FFFFFF; padding: 30px; border-top: 3px solid #E1000F; border-bottom: 8px solid #000091; }
                    .signature { margin-top: 35px; padding: 20px; background-color: #FFFFFF; border-left: 4px solid #000091; }
                    .signature-name { font-weight: 700; color: #000091; margin-bottom: 5px; font-size: 16px; }
                    .signature-title { color: #000091; font-size: 14px; font-weight: 500; }
                    .experimental-notice { background-color: #FFFFFF; border: 2px solid #E1000F; border-left: 6px solid #E1000F; padding: 20px; margin: 25px 0; border-radius: 4px; }
                    .experimental-notice p { margin: 0; color: #E1000F; font-size: 14px; font-weight: 500; }
                </style>
            </head>
            <body>
                <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border: 1px solid #E5E7EB;">
                    <div style="background-color: #000091 !important; height: 8px;"></div>
                    <div style="background-color: #E1000F !important; height: 3px;"></div>
                    
                    <div style="padding: 40px 30px; background-color: #FFFFFF;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #000091 !important; font-size: 26px; font-weight: 700; margin: 0; letter-spacing: -0.5px;">Assistant IA</h1>
                        </div>
                        
                        <p style="font-size: 16px; color: #1F2937; margin-bottom: 20px;">Bonjour,</p>
                        
                        <p style="font-size: 16px; color: #1F2937; line-height: 1.6; margin-bottom: 25px;">
                            Vous pouvez désormais accéder à l'Assistant IA, service opéré par la <strong style="color: #000091 !important;">Direction interministérielle du numérique (DINUM)</strong>.
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://albert.numerique.gouv.fr/" style="background-color: #000091 !important; color: #FFFFFF !important; padding: 16px 32px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: 700; letter-spacing: 0.3px; box-shadow: 0 2px 8px rgba(0,0,145,0.15);">
                                 Accéder à l'Assistant IA
                            </a>
                        </div>
                        
                        <p style="font-size: 16px; color: #1F2937; line-height: 1.6; margin: 25px 0;">
                            Nous vous invitons à rejoindre le canal Tchap de support utilisateur pour nous faire vos retours sur l'utilisation de l'outil.
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://tchap.gouv.fr/#/room/!gpLYRJyIwdkcHBGYeC:agent.dinum.tchap.gouv.fr" style="background-color: #E1000F !important; color: #FFFFFF !important; padding: 14px 28px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: 700; letter-spacing: 0.3px; box-shadow: 0 2px 8px rgba(225,0,15,0.15);">
                                💬 Rejoindre le canal Tchap
                            </a>
                        </div>
                        
                        <div style="background-color: #FFFFFF; border: 2px solid #E1000F; border-left: 6px solid #E1000F; padding: 20px; margin: 25px 0; border-radius: 4px;">
                            <p style="margin: 0; color: #E1000F !important; font-size: 14px; font-weight: 500;"><strong>⚠️ Phase d'expérimentation</strong></p>
                            <p style="margin: 8px 0 0 0; color: #E1000F !important; font-size: 14px; font-weight: 500;">Celui-ci est encore en phase d'expérimentation. Nous apportons une importance toute particulière à vos retours, et vous informons que des changements importants d'interface et de fonctionnalités avancées pourront avoir lieu dans les prochains mois.</p>
                        </div>
                        
                        <div style="margin-top: 35px; padding: 20px; background-color: #FFFFFF; border-left: 4px solid #000091;">
                            <p style="margin-bottom: 15px; color: #1F2937;">Bien cordialement,</p>
                            <div style="font-weight: 700; color: #000091 !important; margin-bottom: 5px; font-size: 16px;">Eliott Dugois</div>
                            <div style="color: #000091 !important; font-size: 14px; font-weight: 500;">Responsable du produit Assistant IA</div>
                        </div>
                    </div>
                    
                    <div style="background-color: #FFFFFF; padding: 15px 20px; border-top: 3px solid #E1000F; border-bottom: 8px solid #000091;">
                        <p style="margin: 0; font-size: 11px; color: #6B7280; text-align: center;">
                            Cet email a été envoyé automatiquement. Merci de ne pas répondre à cette adresse.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Create plain text version
            text_body = """
==========================================================
ASSISTANT IA
==========================================================

Bonjour,

Vous pouvez désormais accéder à l'Assistant IA, service opéré par la Direction interministérielle du numérique (DINUM) !

🚀 Accéder à l'Assistant IA :
https://albert.numerique.gouv.fr/

Nous vous invitons à rejoindre le canal Tchap de support utilisateur pour nous faire vos retours sur l'utilisation de l'outil.

💬 Rejoindre le canal Tchap :
https://tchap.gouv.fr/#/room/!gpLYRJyIwdkcHBGYeC:agent.dinum.tchap.gouv.fr

⚠️ PHASE D'EXPÉRIMENTATION
Celui-ci est encore en phase d'expérimentation. Nous apportons une importance toute particulière à vos retours, et vous informons que des changements importants d'interface et de fonctionnalités avancées pourront avoir lieu dans les prochains mois.

Bien cordialement,

Eliott Dugois
Responsable du produit Assistant IA

----------------------------------------------------------
Direction interministérielle du numérique (DINUM)
Service public numérique de l'État français

Cet email a été envoyé automatiquement.
Merci de ne pas répondre à cette adresse.
==========================================================
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
