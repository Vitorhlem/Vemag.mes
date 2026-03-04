import enum
from sqlalchemy import Column, Integer, String, LargeBinary 
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Sector(str, enum.Enum):
    MANUFATURA = "manufatura"


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    sector = Column(String(50), nullable=False)
    cnpj = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    website = Column(String(100), nullable=True)
    users = relationship("User", back_populates="organization")
    machines = relationship("Machine", back_populates="organization")
    tools = relationship("Tool", back_populates="organization")
    alerts = relationship("Alert", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
