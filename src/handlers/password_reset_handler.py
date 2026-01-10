"""Password reset event handlers."""
from src.events.domain import IEventHandler, DomainEvent, EventResult
from src.events.security_events import (
    PasswordResetRequestEvent,
    PasswordResetExecuteEvent,
)
from src.services.password_reset_service import PasswordResetService
from src.services.email_service import EmailService


class PasswordResetHandler(IEventHandler):
    """
    Handles password reset events.

    Flow:
    1. Route emits event → 2. This handler receives it → 3. Calls service → 4. Side effects
    """

    def __init__(
        self,
        password_reset_service: PasswordResetService,
        email_service: EmailService,
        activity_logger,
        reset_url_base: str = "https://app.example.com/reset-password",
    ):
        """
        Initialize handler with dependencies.

        Args:
            password_reset_service: Service for password reset logic
            email_service: Service for sending emails
            activity_logger: Logger for activity tracking
            reset_url_base: Base URL for reset links
        """
        self._reset_service = password_reset_service
        self._email_service = email_service
        self._activity_logger = activity_logger
        self._reset_url_base = reset_url_base

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler can handle the event."""
        return isinstance(event, (PasswordResetRequestEvent, PasswordResetExecuteEvent))

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle the event by routing to appropriate method.

        Args:
            event: The event to handle

        Returns:
            EventResult with success/failure status
        """
        if isinstance(event, PasswordResetRequestEvent):
            return self.handle_reset_request(event)
        elif isinstance(event, PasswordResetExecuteEvent):
            return self.handle_reset_execute(event)
        else:
            return EventResult.error_result("Unknown event type")

    def handle_reset_request(self, event: PasswordResetRequestEvent) -> EventResult:
        """
        Handle password reset request.

        1. Call service to create token
        2. Send email if user exists
        3. Log activity

        Args:
            event: PasswordResetRequestEvent with email and request_ip

        Returns:
            EventResult (always success to not reveal if email exists)
        """
        # Call service
        result = self._reset_service.create_reset_token(event.email)

        if result.success and result.token:
            # User exists - send email
            reset_url = f"{self._reset_url_base}?token={result.token}"

            self._email_service.send_template(
                to=result.email,
                template="password_reset",
                context={
                    "reset_url": reset_url,
                    "expires_in": "1 hour",
                },
            )

            self._activity_logger.log(
                action="password_reset_requested",
                user_id=result.user_id,
                metadata={"ip": event.request_ip},
            )

        # Always return success (don't reveal if email exists)
        return EventResult.success_result(
            {"message": "If email exists, reset link sent"}
        )

    def handle_reset_execute(self, event: PasswordResetExecuteEvent) -> EventResult:
        """
        Handle password reset execution.

        1. Call service to reset password
        2. Send confirmation or log failure

        Args:
            event: PasswordResetExecuteEvent with token and new_password

        Returns:
            EventResult with success/failure
        """
        result = self._reset_service.reset_password(event.token, event.new_password)

        if result.success:
            # Send confirmation email
            self._email_service.send_template(
                to=result.email, template="password_changed", context={}
            )

            self._activity_logger.log(
                action="password_reset_completed",
                user_id=result.user_id,
                metadata={"ip": event.reset_ip},
            )

            return EventResult.success_result({"message": "Password reset successful"})
        else:
            # Log failed attempt
            self._activity_logger.log(
                action="password_reset_failed",
                metadata={
                    "reason": result.failure_reason,
                    "ip": event.reset_ip,
                    "token_prefix": event.token[:8] + "..."
                    if len(event.token) > 8
                    else event.token,
                },
            )

            return EventResult.error_result(
                error=result.error, error_type=result.failure_reason
            )
