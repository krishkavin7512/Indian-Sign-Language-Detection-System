from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Recognition(Base):
    __tablename__ = "recognitions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    sign_label = Column(String(256))
    sign_label_hindi = Column(String(256), nullable=True)
    confidence = Column(Float)
    model_used = Column(String(64))
