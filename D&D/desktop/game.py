from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
from contextlib import closing

from sqlalchemy import select

from backend import models, schemas, services
from backend.database import Base, build_engine, session_factory
from .source_data import workspace_candidates


class GameStore:
    def __init__(self):
        local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        self.data_dir = Path(os.environ.get("ARCANUM_DATA_DIR", local / "Arcanum"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        target = self.data_dir / "arcanum.sqlite3"
        if not target.exists() and not os.environ.get("ARCANUM_DATA_DIR"):
            previous = next((root / "data" / "arcanum.sqlite3" for root in workspace_candidates()
                             if (root / "data" / "arcanum.sqlite3").is_file()), None)
            if previous:
                with closing(sqlite3.connect(previous.resolve().as_uri() + "?mode=ro", uri=True)) as old:
                    with closing(sqlite3.connect(target)) as new:
                        old.backup(new)
        self.engine = build_engine(f"sqlite:///{target.as_posix()}")
        Base.metadata.create_all(self.engine)
        self.sessions = session_factory(self.engine)

    @contextmanager
    def reading(self):
        with self.sessions() as session:
            session.connection().exec_driver_sql("BEGIN")
            yield session

    def characters(self):
        with self.reading() as db:
            rows = db.scalars(select(models.Character))
            return sorted((services.character_out(row) for row in rows), key=lambda item: item["name"].casefold())

    def parties(self):
        with self.reading() as db:
            return [services.party_out(db, row) for row in db.scalars(select(models.Party))]

    def combats(self):
        with self.reading() as db:
            return [services.combat_out(db, row) for row in db.scalars(select(models.Combat))]

    def events(self, combat_id):
        with self.reading() as db:
            query = select(models.CombatEvent).where(models.CombatEvent.combat_id == combat_id)
            return [services.event_out(row) for row in db.scalars(query.order_by(models.CombatEvent.sequence))]

    def character(self, data):
        with self.sessions.begin() as db:
            return services.create_character(db, schemas.CharacterCreate(**data))

    def party(self, data):
        with self.sessions.begin() as db:
            return services.create_party(db, schemas.PartyCreate(**data))

    def encounter(self, party_id, monster_count):
        if not 1 <= monster_count <= 12:
            raise ValueError("Escolha entre 1 e 12 monstros.")
        data = schemas.CombatCreate(party_id=party_id, monster_ids=["training-goblin"] * monster_count)
        with self.sessions.begin() as db:
            return services.start_combat(db, data)

    def action(self, combat_id, data):
        with self.sessions.begin() as db:
            return services.act(db, combat_id, schemas.CombatAction(**data))

    def rest(self, character_id):
        with self.sessions.begin() as db:
            return services.training_rest(db, character_id)

    def roll(self, expression, mode):
        with self.sessions.begin() as db:
            return services.log_roll(db, expression, mode)
