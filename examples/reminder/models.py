from datetime import datetime
from sqlalchemy import INT, NVARCHAR, Column, DateTime
from avril.models import Base, get_uuid


# リマインド項目のモデル
class ReminderItem(Base):
    __tablename__ = "reminder_items"
    id = Column("id", NVARCHAR(255), default=get_uuid, primary_key=True)
    updated_at = Column("updated_at", DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    remind_to = Column("remind_to", NVARCHAR(255), nullable=False)
    remind_at = Column("remind_at", DateTime, nullable=False, index=True)
    remind_text = Column("remind_text", NVARCHAR(), nullable=False)
    reminded = Column("reminded", INT, default=0, index=True)
