from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.sql import func
import uuid
from app.database import Base


class ProcessingJob(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    file_path = Column(String(512))
    status = Column(String(32), default="queued")
    progress = Column(Float, default=0.0)
    result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
