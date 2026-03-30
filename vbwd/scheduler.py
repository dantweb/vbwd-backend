"""APScheduler for core background jobs (booking completion only).

Subscription lifecycle jobs moved to plugins/subscription/subscription/scheduler.py.
"""
import logging
from vbwd.extensions import db

logger = logging.getLogger(__name__)


def _run_booking_completion_jobs(app):
    """Auto-complete bookings whose time has passed."""
    with app.app_context():
        try:
            from plugins.booking.booking.repositories.booking_repository import (
                BookingRepository,
            )
            from plugins.booking.booking.repositories.resource_repository import (
                ResourceRepository,
            )
            from plugins.booking.booking.services.booking_completion_service import (
                BookingCompletionService,
            )
            from vbwd.events.bus import event_bus

            service = BookingCompletionService(
                booking_repository=BookingRepository(db.session),
                resource_repository=ResourceRepository(db.session),
                event_bus=event_bus,
            )
            completed = service.complete_past_bookings()
            if completed:
                db.session.commit()
                logger.info("[Scheduler] Auto-completed %d booking(s)", len(completed))
        except ImportError:
            pass  # Booking plugin not installed


def start_booking_scheduler(app):
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_booking_completion_jobs,
        "interval",
        seconds=900,
        args=[app],
        id="booking_completion_jobs",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] Booking completion scheduler started")
    return scheduler
