"""UserCase domain model."""
from sqlalchemy.dialects.postgresql import UUID
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import UserCaseStatus


class UserCase(BaseModel):
    """
    User case/project model.

    Stores case descriptions for subscriptions.
    """

    __tablename__ = "user_case"

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = db.Column(db.Text)
    date_started = db.Column(db.Date)
    status = db.Column(
        db.Enum(
            UserCaseStatus,
            name="usercasestatus",
            native_enum=True,
            create_constraint=False,
        ),
        nullable=False,
        default=UserCaseStatus.DRAFT,
        index=True,
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,
            "date_started": self.date_started.isoformat()
            if self.date_started
            else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<UserCase(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
