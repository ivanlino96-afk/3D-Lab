from collections.abc import Callable, Iterable

from src.audit.infrastructure.repository import SqlAlchemyAuditRepository
from src.notifications.application.deliver_notifications import DeliverNotifications
from src.notifications.infrastructure.email_gateway import SmtpEmailGateway
from src.notifications.infrastructure.repository import SqlAlchemyNotificationRepository
from src.notifications.presentation.templates import SpanishEmailTemplates
from src.retention.application.expire_quote_files import ExpireQuoteFiles
from src.retention.infrastructure.repository import SqlAlchemyQuoteFileRetentionRepository
from src.shared.config import get_settings
from src.shared.domain.types import utc_now
from src.shared.infrastructure.database import SessionFactory
from src.shared.infrastructure.private_storage import FileSystemPrivateStorage

Job = Callable[[], None]


def run_jobs(jobs: Iterable[Job]) -> None:
    """Run registered jobs; concrete schedules are configured outside the domain."""
    for job in jobs:
        job()


def expire_quote_files_job() -> None:
    with SessionFactory.begin() as session:
        ExpireQuoteFiles(
            repository=SqlAlchemyQuoteFileRetentionRepository(session),
            storage=FileSystemPrivateStorage(get_settings().private_storage_root),
            audit=SqlAlchemyAuditRepository(session),
        ).execute(utc_now())


def deliver_notifications_job() -> None:
    settings = get_settings()
    with SessionFactory.begin() as session:
        DeliverNotifications(
            SqlAlchemyNotificationRepository(session),
            SmtpEmailGateway(
                settings.smtp_host,
                settings.smtp_port,
                settings.smtp_username,
                settings.smtp_password,
                settings.smtp_from,
            ),
            SpanishEmailTemplates(),
        ).execute(utc_now())


def main() -> None:
    run_jobs((deliver_notifications_job, expire_quote_files_job))


if __name__ == "__main__":
    main()
