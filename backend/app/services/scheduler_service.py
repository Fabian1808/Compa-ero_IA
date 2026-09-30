from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.config import settings
from app.database import async_session_maker
from app.models.account import Account, AccountStatus
from app.models.user import User
from app.services.sync_service import SyncService
from app.services.blocker_detection import BlockerDetector

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._started = False

    def start(self) -> None:
        if self._started:
            return

        # Sync job - every 5 minutes
        self.scheduler.add_job(
            self._sync_all_accounts_job,
            IntervalTrigger(minutes=settings.sync_interval_minutes),
            id="sync_all_accounts",
            replace_existing=True,
        )

        # Daily briefing - at configured hour
        self.scheduler.add_job(
            self._daily_briefing_job,
            CronTrigger(hour=settings.daily_briefing_hour, minute=0),
            id="daily_briefing",
            replace_existing=True,
        )

        # End of day - at configured hour
        self.scheduler.add_job(
            self._end_of_day_job,
            CronTrigger(hour=settings.end_of_day_hour, minute=0),
            id="end_of_day",
            replace_existing=True,
        )

        # Notification check - every minute
        self.scheduler.add_job(
            self._check_notifications_job,
            IntervalTrigger(minutes=settings.notification_check_interval_minutes),
            id="check_notifications",
            replace_existing=True,
        )

        # Blocker detection - every 15 minutes
        self.scheduler.add_job(
            self._blocker_detection_job,
            IntervalTrigger(minutes=15),
            id="blocker_detection",
            replace_existing=True,
        )

        self.scheduler.start()
        self._started = True
        logger.info("Scheduler started")

    def stop(self) -> None:
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            logger.info("Scheduler stopped")

    async def _sync_all_accounts_job(self) -> None:
        """Background job to sync all active accounts."""
        async with async_session_maker() as db:
            result = await db.execute(select(Account).where(Account.status == AccountStatus.ACTIVE))
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    sync_service = SyncService(db)
                    async for _ in sync_service.sync_account(account.id):
                        pass  # Just iterate to completion
                except Exception as e:
                    logger.error(f"Scheduled sync failed for account {account.id}: {e}")

    async def _daily_briefing_job(self) -> None:
        """Generate daily briefing for all users."""
        # TODO: Implement when notification service is ready
        logger.info("Daily briefing job triggered")

    async def _end_of_day_job(self) -> None:
        """Generate end of day summary for all users."""
        # TODO: Implement when notification service is ready
        logger.info("End of day job triggered")

    async def _check_notifications_job(self) -> None:
        """Check for deadline/meeting notifications."""
        # TODO: Implement when notification service is ready
        pass

    async def _blocker_detection_job(self) -> None:
        """Run blocker detection for all users."""
        async with async_session_maker() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    detector = BlockerDetector(db, user.id)
                    await detector.schedule_blocker_check()
                    await db.commit()
                except Exception as e:
                    logger.error(f"Blocker detection failed for user {user.id}: {e}")
                    await db.rollback()