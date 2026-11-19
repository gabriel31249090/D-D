"""Authoritative transactions for the first local combat slice."""
import secrets
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from .models import Character, Combat, Combatant, CombatEvent, DiceLog, Party, PartyMember
from .rules import TRAINING_MONSTER, character_stats, resolve_attack, roll, roll_die
from .schemas import CharacterCreate, CombatAction, CombatCreate, PartyCreate


class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


def require(db: Session, model, object_id):
    obj = db.get(model, object_id)
    if obj is None:
        raise DomainError("not_found", f"{model.__name__} not found", 404)
    return obj


def character_out(character: Character) -> dict:
    data = CharacterCreate.model_validate(character.sheet)
    return {**data.model_dump(), **character_stats(data), "id": character.id,
            "max_hp": character.max_hp, "current_hp": character.current_hp,
            "active_combat_id": character.active_combat_id}


def create_character(db: Session, data: CharacterCreate):
    stats = character_stats(data)
    character = Character(sheet=data.model_dump(), max_hp=stats["max_hp"], current_hp=stats["max_hp"])
    db.add(character)
    db.flush()
    return character_out(character)


def party_out(db: Session, party: Party):
    return {"id": party.id, "name": party.name, "character_ids": list(db.scalars(
        select(PartyMember.character_id).where(PartyMember.party_id == party.id).order_by(PartyMember.character_id)))}


def create_party(db: Session, data: PartyCreate):
    for character_id in data.character_ids:
        require(db, Character, character_id)
    party = Party(name=data.name)
    db.add(party)
    db.flush()
    db.add_all([PartyMember(party_id=party.id, character_id=character_id) for character_id in data.character_ids])
    db.flush()
    return party_out(db, party)


def actors_for(db: Session, combat_id: str):
    return list(db.scalars(select(Combatant).where(Combatant.combat_id == combat_id).order_by(Combatant.order_index)))


def actor_out(actor: Combatant):
    return {"id": actor.id, "character_id": actor.character_id, "name": actor.profile["name"], "team": actor.team,
            "max_hp": actor.max_hp, "current_hp": actor.current_hp, "armor_class": actor.profile["armor_class"],
            "initiative": actor.initiative, "initiative_roll": actor.initiative_roll,
            "action_available": actor.action_available and actor.current_hp > 0,
            "conditions": [] if actor.current_hp > 0 else ["unconscious", "incapacitated"],
            "attacks": actor.profile["attacks"], "is_example": actor.profile["is_example"]}


def combat_out(db: Session, combat: Combat):
    return {"id": combat.id, "party_id": combat.party_id, "rule_set": combat.rule_set, "mode": "local_arena",
            "status": combat.status, "version": combat.version, "round": combat.round,
            "current_actor_id": combat.current_actor_id, "winner": combat.winner,
            "combatants": [actor_out(actor) for actor in actors_for(db, combat.id)]}


def event_out(event: CombatEvent):
    return {"id": event.id, "combat_id": event.combat_id, "sequence": event.sequence,
            "type": event.type, "payload": event.payload}


def emit(db: Session, combat: Combat, kind: str, payload: dict):
    previous = db.scalar(select(func.max(CombatEvent.sequence)).where(CombatEvent.combat_id == combat.id)) or 0
    event = CombatEvent(combat_id=combat.id, sequence=previous+1, type=kind, payload=payload)
    db.add(event)
    db.flush()
    return event_out(event)


def start_combat(db: Session, data: CombatCreate, randbelow=secrets.randbelow):
    party = require(db, Party, data.party_id)
    ids = party_out(db, party)["character_ids"]
    if not ids:
        raise DomainError("empty_party", "Party must contain characters")
    combat = Combat(party_id=party.id, rule_set=data.rule_set)
    db.add(combat)
    db.flush()
    actors = []
    # Sorted locks prevent opposite party member order from deadlocking on PostgreSQL.
    for character_id in sorted(ids):
        claimed = db.execute(update(Character).where(Character.id == character_id,
            Character.active_combat_id.is_(None), Character.current_hp > 0).values(active_combat_id=combat.id))
        if claimed.rowcount != 1:
            raise DomainError("character_unavailable", "Character is incapacitated or already in an active combat")
        character = require(db, Character, character_id)
        sheet = character_out(character)
        initiative_roll = roll_die(20, randbelow)
        actors.append(Combatant(combat_id=combat.id, character_id=character.id,
            profile={"name": sheet["name"], "armor_class": sheet["armor_class"], "attacks": sheet["attacks"],
                     "is_example": False, "initiative_bonus": sheet["initiative_bonus"]},
            team="party", max_hp=character.max_hp, current_hp=character.current_hp,
            initiative=initiative_roll+sheet["initiative_bonus"], initiative_roll=initiative_roll))
    for number, monster_id in enumerate(data.monster_ids, 1):
        monster = TRAINING_MONSTER
        initiative_roll = roll_die(20, randbelow)
        actors.append(Combatant(combat_id=combat.id, character_id=None,
            profile={"name": f"{monster['name']} {number}", "armor_class": monster["armor_class"],
                     "attacks": monster["attacks"], "is_example": True,
                     "initiative_bonus": monster["dexterity_modifier"]},
            team="enemy", max_hp=monster["max_hp"], current_hp=monster["max_hp"],
            initiative=initiative_roll+monster["dexterity_modifier"], initiative_roll=initiative_roll))
    # Equal totals are resolved by stable creation order, a documented local DM tie decision.
    actors.sort(key=lambda actor: -actor.initiative)
    for index, actor in enumerate(actors):
        actor.order_index = index
        db.add(actor)
    db.flush()
    combat.current_actor_id = actors[0].id
    db.flush()
    snapshot = combat_out(db, combat)
    emit(db, combat, "combat_started", {"snapshot": snapshot, "tie_break": "stable_creation_order"})
    return snapshot


def act(db: Session, combat_id: str, data: CombatAction, randbelow=secrets.randbelow):
    # The first statement obtains the combat write lock and checks the version atomically.
    changed = db.execute(update(Combat).where(Combat.id == combat_id, Combat.status == "active",
        Combat.version == data.expected_version).values(version=Combat.version+1))
    if changed.rowcount != 1:
        require(db, Combat, combat_id)
        raise DomainError("stale_combat", "Combat finished or version changed; reload its snapshot")
    combat = require(db, Combat, combat_id)
    actors = actors_for(db, combat_id)
    by_id = {actor.id: actor for actor in actors}
    actor = by_id.get(data.actor_id)
    if actor is None or actor.id != combat.current_actor_id or actor.current_hp <= 0:
        raise DomainError("invalid_turn", "Only the current conscious actor may act")
    events = []
    if data.type == "attack":
        if not actor.action_available:
            raise DomainError("action_spent", "The attack action has already been used this turn")
        target = by_id.get(data.target_id)
        if target is None or target.team == actor.team or target.current_hp <= 0:
            raise DomainError("invalid_target", "Target must be an active opponent in this combat")
        attack = next((item for item in actor.profile["attacks"] if item["id"] == data.attack_id), None)
        if attack is None:
            raise DomainError("invalid_attack", "This actor does not have that attack")
        resolved = resolve_attack(attack, target.profile["armor_class"], randbelow)
        hp_before = target.current_hp
        target.current_hp = max(0, target.current_hp-resolved["damage"])
        actor.action_available = False
        if target.character_id:
            require(db, Character, target.character_id).current_hp = target.current_hp
        events.append(emit(db, combat, "attack_resolved", {"actor_id": actor.id, "target_id": target.id,
            "attack_id": attack["id"], **resolved, "hp_before": hp_before, "hp_after": target.current_hp,
            "version": combat.version}))
        alive_teams = {item.team for item in actors if item.current_hp > 0}
        if len(alive_teams) == 1:
            combat.status = "completed"
            combat.winner = next(iter(alive_teams))
            combat.current_actor_id = None
            for participant in actors:
                if participant.character_id:
                    character = require(db, Character, participant.character_id)
                    character.current_hp = participant.current_hp
                    character.active_combat_id = None
            events.append(emit(db, combat, "combat_completed", {"winner": combat.winner,
                "final_hp": {item.id: item.current_hp for item in actors}, "version": combat.version}))
    else:
        next_actor = None
        for offset in range(1, len(actors)+1):
            candidate = actors[(actor.order_index+offset) % len(actors)]
            if candidate.current_hp > 0:
                next_actor = candidate
                break
        if next_actor.order_index <= actor.order_index:
            combat.round += 1
        next_actor.action_available = True
        combat.current_actor_id = next_actor.id
        events.append(emit(db, combat, "turn_started", {"actor_id": next_actor.id, "round": combat.round,
            "version": combat.version}))
    db.flush()
    return {"combat": combat_out(db, combat), "events": events}


def training_rest(db: Session, character_id: str):
    changed = db.execute(update(Character).where(Character.id == character_id,
        Character.active_combat_id.is_(None)).values(current_hp=Character.max_hp))
    character = require(db, Character, character_id)
    if changed.rowcount != 1:
        raise DomainError("character_busy", "Cannot reset training HP during an active combat")
    db.flush()
    return character_out(character)


def log_roll(db: Session, expression, mode, randbelow=secrets.randbelow):
    try:
        result = roll(expression, mode, randbelow).model_dump()
    except ValueError as error:
        raise DomainError("invalid_dice", str(error), 422) from error
    entry = DiceLog(result=result)
    db.add(entry)
    db.flush()
    return {"id": entry.id, **result}

