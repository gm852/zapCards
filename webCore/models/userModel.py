
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Boolean, DateTime, Column, JSON
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .session import Base



class User(Base):
	__tablename__ = 'users'
 
	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	internalID: Mapped[str] = mapped_column(String(64), nullable=False)
	username: Mapped[str] = mapped_column(String(64), nullable=False)
	password: Mapped[str] = mapped_column(String(256), nullable=False)
	decksJson: Mapped[str] = mapped_column(JSON, nullable=False)
	created: Mapped[str] = mapped_column(String(64), nullable=False)
	role: Mapped[str] = mapped_column(String(64), nullable=False)
	lastLogin: Mapped[str] = mapped_column(String(64), nullable=True)
	deleted: Mapped[bool] = mapped_column(Boolean, nullable=False)
 
