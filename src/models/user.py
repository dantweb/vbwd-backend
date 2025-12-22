"""User domain model."""
from sqlalchemy.dialects.postgresql import UUID
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import UserStatus, UserRole


class User(BaseModel):
    """
    User account model.

    Stores core authentication data. Personal details
    are stored separately in UserDetails for GDPR compliance.
    """

    __tablename__ = "user"

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING,
        index=True,
    )
    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
    )

    # Relationships
    details = db.relationship(
        "UserDetails",
        backref="user",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan",
    )
    subscriptions = db.relationship(
        "Subscription",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    invoices = db.relationship(
        "UserInvoice",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    cases = db.relationship(
        "UserCase",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    def to_dict(self) -> dict:
        """
        Convert to dictionary, excluding sensitive data.

        Returns:
            Dictionary representation without password_hash.
        """
        return {
            "id": self.id,
            "email": self.email,
            "status": self.status.value,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
