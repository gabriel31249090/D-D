"""Local development API; run with scripts/run_api.ps1, bound to loopback."""
from collections.abc import Callable
from contextlib import asynccontextmanager
import secrets
from typing import Annotated
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from .database import Base, build_engine, database_url, session_factory
from .models import Character, Combat, CombatEvent, Party
from .rules import TRAINING_MONSTER
from .schemas import (ActionResult, CharacterCreate, CharacterOut, CombatAction, CombatCreate,
    CombatOut, DiceOut, DiceRequest, EventOut, HealthOut, MonsterOut, PartyCreate, PartyOut)
from .services import (DomainError, act, character_out, combat_out, create_character, create_party,
    event_out, log_roll, party_out, require, start_combat, training_rest)

ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"]


def create_app(url: str | None = None, *, initialize_schema: bool = False,
               randbelow: Callable[[int], int] = secrets.randbelow) -> FastAPI:
    engine = build_engine(url or database_url())
    sessions = session_factory(engine)

    @asynccontextmanager
    async def lifespan(app):
        # Tests opt in to isolated schema creation; normal use requires Alembic.
        if initialize_schema:
            Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title="ARCANUM local core", version="0.1.0", lifespan=lifespan,
                  description="Local development only. Level-1 fighter numeric subset, training arena; no authentication or multiplayer.")
    app.state.engine = engine
    app.state.sessions = sessions
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
    app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type"])

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin is not None and origin not in ORIGINS:
            return JSONResponse({"detail": {"code": "origin_denied", "message": "Only local development origins are allowed"}}, status_code=403)
        return await call_next(request)

    def get_db():
        with sessions() as db:
            try:
                yield db
            except BaseException:
                db.rollback()
                raise

    DB = Annotated[Session, Depends(get_db)]

    @app.exception_handler(DomainError)
    async def domain_error(request, error):
        return JSONResponse({"detail": {"code": error.code, "message": error.message}}, status_code=error.status)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, error):
        return JSONResponse({"detail": {"code": "conflicting_write", "message": "Conflicting data; reload and retry"}}, status_code=409)

    @app.exception_handler(OperationalError)
    async def storage_error(request, error):
        return JSONResponse({"detail": {"code": "storage_unavailable", "message": "Database unavailable; check migrations and local logs"}}, status_code=503)

    @app.get("/health", response_model=HealthOut)
    def health():
        ready = inspect(engine).has_table("characters")
        if not ready:
            raise DomainError("migration_required", "Run python -m alembic upgrade head", 503)
        return {"ok": True}

    @app.post("/api/characters", response_model=CharacterOut, status_code=201)
    def character_create(data: CharacterCreate, db: DB):
        result = create_character(db, data)
        db.commit()
        return result

    @app.get("/api/characters", response_model=list[CharacterOut])
    def characters(db: DB, limit: Annotated[int, Query(ge=1, le=100)] = 50,
                   offset: Annotated[int, Query(ge=0)] = 0):
        return [character_out(item) for item in db.scalars(select(Character).order_by(Character.id).offset(offset).limit(limit))]

    @app.get("/api/characters/{character_id}", response_model=CharacterOut)
    def character_get(character_id: str, db: DB):
        return character_out(require(db, Character, character_id))

    @app.post("/api/characters/{character_id}/rest", response_model=CharacterOut,
              summary="Reset training HP outside combat (not a full rest rules implementation)")
    def rest(character_id: str, db: DB):
        result = training_rest(db, character_id)
        db.commit()
        return result

    @app.post("/api/parties", response_model=PartyOut, status_code=201)
    def party_create(data: PartyCreate, db: DB):
        result = create_party(db, data)
        db.commit()
        return result

    @app.get("/api/parties", response_model=list[PartyOut])
    def parties(db: DB, limit: Annotated[int, Query(ge=1, le=100)] = 50,
                offset: Annotated[int, Query(ge=0)] = 0):
        return [party_out(db, item) for item in db.scalars(select(Party).order_by(Party.id).offset(offset).limit(limit))]

    @app.get("/api/parties/{party_id}", response_model=PartyOut)
    def party_get(party_id: str, db: DB):
        return party_out(db, require(db, Party, party_id))

    @app.get("/api/monsters", response_model=list[MonsterOut])
    def monsters():
        return [TRAINING_MONSTER]

    @app.post("/api/combat", response_model=CombatOut, status_code=201)
    def combat_create(data: CombatCreate, db: DB):
        result = start_combat(db, data, randbelow)
        db.commit()
        return result

    @app.get("/api/combat", response_model=list[CombatOut])
    def combats(db: DB, limit: Annotated[int, Query(ge=1, le=100)] = 50,
                offset: Annotated[int, Query(ge=0)] = 0):
        return [combat_out(db, item) for item in db.scalars(select(Combat).order_by(Combat.id).offset(offset).limit(limit))]

    @app.get("/api/combat/{combat_id}", response_model=CombatOut)
    def combat_get(combat_id: str, db: DB):
        return combat_out(db, require(db, Combat, combat_id))

    @app.post("/api/combat/{combat_id}/actions", response_model=ActionResult)
    def action(combat_id: str, data: CombatAction, db: DB):
        result = act(db, combat_id, data, randbelow)
        db.commit()
        return result

    @app.get("/api/combat/{combat_id}/events", response_model=list[EventOut])
    def events(combat_id: str, db: DB, after_sequence: Annotated[int, Query(ge=0)] = 0,
               limit: Annotated[int, Query(ge=1, le=500)] = 200):
        require(db, Combat, combat_id)
        return [event_out(item) for item in db.scalars(select(CombatEvent).where(CombatEvent.combat_id == combat_id,
            CombatEvent.sequence > after_sequence).order_by(CombatEvent.sequence).limit(limit))]

    @app.post("/api/dice/roll", response_model=DiceOut, status_code=201)
    def dice(data: DiceRequest, db: DB):
        result = log_roll(db, data.expression, data.mode, randbelow)
        db.commit()
        return result

    return app


app = create_app()

