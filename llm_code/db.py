from pathlib import Path
from typing import Optional

from sqlalchemy import Column, DateTime, Engine, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class DBModel(Base):
    __tablename__ = "db_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model: Mapped[str]
    temperature: Mapped[float]
    max_tokens: Mapped[int]
    system_message: Mapped[str]
    user_message: Mapped[str]
    assistant_message: Mapped[str]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]


class Database:
    _engine = None

    @classmethod
    def get(cls, path: Path) -> Engine:
        if cls._engine is not None:
            return cls._engine

        db_url = f"sqlite:///{path}"
        cls._engine = create_engine(db_url)
        Base.metadata.create_all(cls._engine)
        return cls._engine

    @classmethod
    def session(cls):
        assert cls._engine is not None
        return Session(cls._engine)


def get_last_inserted_row() -> Optional[DBModel]:
    with Database.session() as s:
        return s.query(DBModel).order_by(DBModel.id.desc()).first()


def write(
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    system_message: str,
    user_message: str,
    assistant_message: str,
    input_tokens: int,
    output_tokens: int,
):
    db_entry = DBModel(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system_message=system_message,
        user_message=user_message,
        assistant_message=assistant_message,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    with Database.session() as s:
        s.add(db_entry)
        s.commit()
