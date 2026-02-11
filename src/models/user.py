"""User domain model."""
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
    payment_customer_id = db.Column(
        db.String(255), unique=True, nullable=True, index=True
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
        # Build name from details
        name = None
        if self.details:
            name_parts = []
            if self.details.first_name:
                name_parts.append(self.details.first_name)
            if self.details.last_name:
                name_parts.append(self.details.last_name)
            name = " ".join(name_parts) if name_parts else None

        result = {
            "id": str(self.id),
            "email": self.email,
            "name": name,
            "status": self.status.value,
            "is_active": self.is_active,
            "role": self.role.value,
            "roles": [self.role.value],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Include details object for balance and other user details
        if self.details:
            result["details"] = self.details.to_dict()

        return result

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
