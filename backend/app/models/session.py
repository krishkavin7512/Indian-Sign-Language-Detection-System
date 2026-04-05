from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
import uuid
from app.database import Base


class RecognitionSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    mode = Column(SAEnum("alphabet", "number", "word", "sentence", "auto", name="mode_enum"), default="auto")
    input_type = Column(SAEnum("webcam", "upload", name="input_enum"), default="webcam")
    status = Column(SAEnum("active", "completed", "error", name="status_enum"), default="active")
