
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Boolean, DateTime, Column, JSON
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .session import Base


		
class Deck(Base):
	__tablename__ = 'decks'

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	deckID: Mapped[str] = mapped_column(String(64), nullable=False)
	ownerID: Mapped[str] = mapped_column(String(64), nullable=False)
	created: Mapped[str] = mapped_column(String(64), nullable=False)
	deleted: Mapped[bool] = mapped_column(Boolean, nullable=False)
	deckJson: Mapped[bool] = mapped_column(JSON, nullable=False)
	deckHash: Mapped[bool] = mapped_column(String(64), nullable=False)


class Tempdeck(Base):
	__tablename__ = 'temp_decks'

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	deckID: Mapped[str] = mapped_column(String(64), nullable=False)
	ownerID: Mapped[str] = mapped_column(String(64), nullable=False)
	created: Mapped[str] = mapped_column(String(64), nullable=False)
	deleted: Mapped[bool] = mapped_column(Boolean, nullable=False)
	deckJson: Mapped[bool] = mapped_column(JSON, nullable=False)
	deckHash: Mapped[bool] = mapped_column(String(64), nullable=False)
