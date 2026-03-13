# backend/models/media_generation.py
# Purpose: SQLAlchemy model for background media generation jobs (video + images)
# NOT for: Generation logic (services/media_gen_worker.py) or API routes

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum
from sqlalchemy.sql import func
from database import Base
from models.jobs import JobStatus


class MediaGeneration(Base):
    """Tracks background media generation jobs (video + A+ images).

    WHY: Decouples generation from request lifecycle — user can navigate away
    while ComfyUI (2-5 min) or LLM+Pillow (15-30s) runs in background.
    """
    __tablename__ = "media_generations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    media_type = Column(String(20), nullable=False)  # "video" or "images"
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)

    # WHY: Full input params for history display + re-generation
    input_params = Column(JSON, default=dict)
    # WHY: base64 images/video — large but acceptable for MVP. Future: Supabase Storage
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    # WHY: User feedback for learning — "za ciemne", "dodaj cechy" etc.
    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<MediaGeneration {self.id}: {self.media_type} {self.status}>"
