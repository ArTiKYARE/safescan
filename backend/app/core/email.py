"""
SafeScan — Email Service
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """Send an email via SMTP."""
    message = MIMEMultipart("alternative")
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject

    if text_content:
        message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))

    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_TLS,
        )
        await smtp.connect()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        await smtp.send_message(message)
        await smtp.quit()
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False


def get_verification_email_html(token: str, domain: str) -> str:
    """Generate HTML for domain verification email."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">SafeScan — Подтверждение владения доменом</h2>
        <p>Вы запросили верификацию домена <strong>{domain}</strong>.</p>
        <p>Используйте один из следующих методов:</p>
        
        <h3>Метод 1: DNS TXT запись</h3>
        <p>Добавьте TXT запись для вашего домена:</p>
        <div style="background: #f3f4f6; padding: 12px; border-radius: 6px; font-family: monospace;">
            _safescan-verify.{domain} TXT "{token}"
        </div>
        
        <h3>Метод 2: Файл верификации</h3>
        <p>Создайте файл по пути <code>/.well-known/safescan-verify.txt</code> с содержимым:</p>
        <div style="background: #f3f4f6; padding: 12px; border-radius: 6px; font-family: monospace;">
            {token}
        </div>
        
        <h3>Метод 3: Email подтверждение</h3>
        <p>Нажмите на ссылку ниже для подтверждения:</p>
        <a href="{settings.APP_CORS_ORIGINS.split(',')[0]}/verify/email?token={token}"
           style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px;
                  text-decoration: none; border-radius: 6px; margin: 12px 0;">
            Подтвердить владение доменом
        </a>
        
        <hr style="margin-top: 24px;">
        <p style="color: #6b7280; font-size: 14px;">
            Если вы не запрачивали верификацию, проигнорируйте это письмо.
        </p>
    </body>
    </html>
    """


def get_welcome_email_html(username: str) -> str:
    """Generate HTML for welcome email."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">Добро пожаловать в SafeScan!</h2>
        <p>Здравствуйте, <strong>{username}</strong>!</p>
        <p>Ваш аккаунт успешно создан. Теперь вы можете:</p>
        <ul>
            <li>Добавить и верифицировать домены</li>
            <li>Запускать сканирование на уязвимости</li>
            <li>Получать детальные отчёты в формате PDF/HTML/JSON</li>
            <li>Интегрировать результаты с SIEM и трекерами</li>
        </ul>
        <p style="color: #6b7280; font-size: 14px;">
            ⚠️ Помните: сканирование разрешено только с согласия владельца ресурса.
        </p>
    </body>
    </html>
    """
