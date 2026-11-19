from uuid import uuid4
from sqlalchemy import ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


def uid():
    return str(uuid4())


class Character(Base):
    __tablename__ = "characters"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    sheet: Mapped[dict] = mapped_column(JSON)
    max_hp: Mapped[int] = mapped_column(Integer)
    current_hp: Mapped[int] = mapped_column(Integer)
    active_combat_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class Party(Base):
    __tablename__ = "parties"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100))


class PartyMember(Base):
    __tablename__ = "party_members"
    party_id: Mapped[str] = mapped_column(ForeignKey("parties.id"), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id"), primary_key=True)


class Combat(Base):
    __tablename__ = "combats"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    party_id: Mapped[str] = mapped_column(ForeignKey("parties.id"))
    rule_set: Mapped[str] = mapped_column(String(30), default="dnd5e-2014")
    status: Mapped[str] = mapped_column(String(20), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    round: Mapped[int] = mapped_column(Integer, default=1)
    current_actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    winner: Mapped[str | None] = mapped_column(String(10), nullable=True)


class Combatant(Base):
    __tablename__ = "combatants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    combat_id: Mapped[str] = mapped_column(ForeignKey("combats.id"), index=True)
    character_id: Mapped[str | None] = mapped_column(ForeignKey("characters.id"), nullable=True)
    profile: Mapped[dict] = mapped_column(JSON)
    team: Mapped[str] = mapped_column(String(10))
    max_hp: Mapped[int] = mapped_column(Integer)
    current_hp: Mapped[int] = mapped_column(Integer)
    initiative: Mapped[int] = mapped_column(Integer)
    initiative_roll: Mapped[int] = mapped_column(Integer)
    order_index: Mapped[int] = mapped_column(Integer)
    action_available: Mapped[bool] = mapped_column(default=True)


class CombatEvent(Base):
    __tablename__ = "combat_events"
    __table_args__ = (UniqueConstraint("combat_id", "sequence"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    combat_id: Mapped[str] = mapped_column(ForeignKey("combats.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)


class DiceLog(Base):
    __tablename__ = "dice_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    result: Mapped[dict] = mapped_column(JSON)

