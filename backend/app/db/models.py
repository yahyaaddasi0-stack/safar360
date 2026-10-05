import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    is_pro = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    balance = relationship("CreditBalance", back_populates="user", uselist=False)

class CreditBalance(Base):
    __tablename__ = "credit_balances"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    free_messages_used = Column(Integer, default=0)
    free_images_used = Column(Integer, default=0)
    last_reset = Column(DateTime, default=datetime.datetime.utcnow)
    pro_credits = Column(Integer, default=0)

    user = relationship("User", back_populates="balance")
