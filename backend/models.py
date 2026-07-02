from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id             = Column(Integer, primary_key=True, index=True)
    title          = Column(String(255))
    description    = Column(Text)
    system         = Column(String(100))

    category       = Column(String(100))
    severity       = Column(String(50))
    recommendation = Column(Text)
    risk_score     = Column(Integer, default=50)
    created_at     = Column(DateTime, default=func.now(), server_default=func.now())