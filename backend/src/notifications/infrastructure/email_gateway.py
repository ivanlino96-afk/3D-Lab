from __future__ import annotations

import smtplib
from email.message import EmailMessage


class SmtpEmailGateway:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    def send(self, recipient: str, subject: str, body: str) -> None:
        if not self.host:
            raise ConnectionError("El servidor de correo no está configurado.")
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=20) as client:
            client.starttls()
            if self.username:
                client.login(self.username, self.password)
            client.send_message(message)
