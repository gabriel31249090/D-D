"""Public API contract. Clients submit intentions, never official roll results."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


Ability = Annotated[int, Field(strict=True, ge=3, le=20)]


class Abilities(Schema):
    strength: Ability = 15
    dexterity: Ability = 14
    constitution: Ability = 13
    intelligence: Ability = 10
    wisdom: Ability = 12
    charisma: Ability = 8


class Equipment(Schema):
    armor: Literal["chain_mail", "leather", "none"] = "chain_mail"
    shield: bool = True
    weapon: Literal["longsword"] = "longsword"


class CharacterCreate(Schema):
    name: str = Field(min_length=1, max_length=100)
    rule_set: Literal["dnd5e-2014"] = "dnd5e-2014"
    class_id: Literal["fighter"] = "fighter"
    level: Literal[1] = 1
    abilities: Abilities = Field(default_factory=Abilities)
    equipment: Equipment = Field(default_factory=Equipment)
    fighting_style: Literal["defense", "dueling"] = "defense"

    @field_validator("level", mode="before")
    @classmethod
    def strict_level(cls, value):
        if type(value) is not int:
            raise ValueError("level must be an integer")
        return value


class AttackProfile(Schema):
    id: str
    name: str
    attack_bonus: int
    damage_expression: str
    damage_type: str
    range_feet: int = 5


class CharacterOut(CharacterCreate):
    id: str
    ability_modifiers: dict[str, int]
    proficiency_bonus: int
    max_hp: int
    current_hp: int
    armor_class: int
    saving_throws: dict[str, int]
    initiative_bonus: int
    attacks: list[AttackProfile]
    active_combat_id: str | None
    scope: str = "level-1 fighter mechanical profile; species/background not implemented"


class PartyCreate(Schema):
    name: str = Field(min_length=1, max_length=100)
    character_ids: list[str] = Field(min_length=1, max_length=12)

    @field_validator("character_ids")
    @classmethod
    def unique_ids(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Duplicate characters are not allowed")
        return value


class PartyOut(PartyCreate):
    id: str


class MonsterOut(Schema):
    id: str
    name: str
    rule_set: str
    is_example: bool
    source: str
    max_hp: int
    armor_class: int
    dexterity_modifier: int
    attacks: list[AttackProfile]


class CombatCreate(Schema):
    party_id: str
    monster_ids: list[Literal["training-goblin"]] = Field(min_length=1, max_length=12)
    rule_set: Literal["dnd5e-2014"] = "dnd5e-2014"


class CombatAction(Schema):
    type: Literal["attack", "end_turn"]
    actor_id: str
    expected_version: int = Field(strict=True, ge=1)
    target_id: str | None = None
    attack_id: Literal["longsword", "training-blade"] | None = None

    @model_validator(mode="after")
    def validate_action(self):
        if self.type == "attack" and (not self.target_id or not self.attack_id):
            raise ValueError("attack requires target_id and attack_id")
        if self.type == "end_turn" and (self.target_id is not None or self.attack_id is not None):
            raise ValueError("end_turn does not accept target_id or attack_id")
        return self


class CombatantOut(Schema):
    id: str
    character_id: str | None
    name: str
    team: Literal["party", "enemy"]
    max_hp: int
    current_hp: int
    armor_class: int
    initiative: int
    initiative_roll: int
    action_available: bool
    conditions: list[str]
    attacks: list[AttackProfile]
    is_example: bool


class CombatOut(Schema):
    id: str
    party_id: str
    rule_set: str
    mode: Literal["local_arena"] = "local_arena"
    status: Literal["active", "completed"]
    version: int
    round: int
    current_actor_id: str | None
    winner: Literal["party", "enemy"] | None
    combatants: list[CombatantOut]


class EventOut(Schema):
    id: int
    combat_id: str
    sequence: int
    type: str
    payload: dict


class ActionResult(Schema):
    combat: CombatOut
    events: list[EventOut]


class DiceRequest(Schema):
    expression: str = Field(min_length=3, max_length=30)
    mode: Literal["normal", "advantage", "disadvantage"] = "normal"


class DiceResult(Schema):
    expression: str
    mode: str
    rolls: list[int]
    kept: list[int]
    modifier: int
    total: int


class DiceOut(DiceResult):
    id: int


class HealthOut(Schema):
    ok: bool
    version: str = "0.1.0"
    mode: str = "local-development"
    authentication: str = "not implemented; bind loopback only"

