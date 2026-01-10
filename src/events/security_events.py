"""Security-related domain events."""
from dataclasses import dataclass, field
from typing import Optional
from src.events.domain import DomainEvent


@dataclass
class PasswordResetRequestEvent(DomainEvent):
    """
    Emitted by route when user requests password reset.

    Flow: Route emits → Handler receives → Handler calls service → Service creates token
    """

    name: str = field(default="security.password_reset.request", init=False)
    email: str = ""
    request_ip: Optional[str] = None


@dataclass
class PasswordResetExecuteEvent(DomainEvent):
    """
    Emitted by route when user submits new password with token.

    Flow: Route emits → Handler receives → Handler calls service → Service resets password
    """

    name: str = field(default="security.password_reset.execute", init=False)
    token: str = ""
    new_password: str = ""
    reset_ip: Optional[str] = None


@dataclass
class LoginFailedEvent(DomainEvent):
    """
    Emitted when login attempt fails.

    Used for security monitoring and brute force protection.
    """

    name: str = field(default="security.login.failed", init=False)
    email: str = ""
    ip: Optional[str] = None
    reason: str = ""  # "invalid_credentials", "inactive_account", etc.
