from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Taxpayer(Base):
    __tablename__ = "taxpayers"
    
    id = Column(Integer, primary_key=True, index=True)
    tin = Column(String(50), unique=True, index=True, nullable=False)
    id_type = Column(String(50), nullable=False)
    id_value = Column(String(100), nullable=False)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Taxpayer(tin='{self.tin}', id_type='{self.id_type}', id_value='{self.id_value}')>"


