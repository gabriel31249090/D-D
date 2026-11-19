"""Small explicitly supported SRD 5.1 numeric subset; no arbitrary code evaluation."""
import re
import secrets
from collections.abc import Callable
from .schemas import AttackProfile, CharacterCreate, DiceResult

RandBelow = Callable[[int], int]
DICE = re.compile(r"([1-9]\d?)d(4|6|8|10|12|20|100)([+-]\d{1,4})?", re.ASCII)


def modifier(score: int) -> int:
    return (score - 10) // 2


def proficiency(level: int) -> int:
    if not 1 <= level <= 20:
        raise ValueError("Level must be between 1 and 20")
    return 2 + (level - 1) // 4


def roll_die(sides: int, randbelow: RandBelow = secrets.randbelow) -> int:
    return randbelow(sides) + 1


def roll(expression: str, mode: str = "normal", randbelow: RandBelow = secrets.randbelow) -> DiceResult:
    match = DICE.fullmatch(expression)
    if not match:
        raise ValueError("Use NdS[+/-M], 1..50 dice, sides 4/6/8/10/12/20/100")
    count, sides = map(int, match.group(1, 2))
    bonus = int(match.group(3) or "0")
    if count > 50 or abs(bonus) > 1000:
        raise ValueError("Dice count or modifier exceeds limits")
    if mode not in ("normal", "advantage", "disadvantage"):
        raise ValueError("Unknown roll mode")
    if mode != "normal" and (count != 1 or sides != 20):
        raise ValueError("Advantage/disadvantage applies only to 1d20")
    values = [roll_die(sides, randbelow) for _ in range(count if mode == "normal" else 2)]
    kept = values if mode == "normal" else [max(values) if mode == "advantage" else min(values)]
    return DiceResult(expression=expression, mode=mode, rolls=values, kept=kept, modifier=bonus, total=sum(kept)+bonus)


def character_stats(data: CharacterCreate) -> dict:
    mods = {k: modifier(v) for k, v in data.abilities.model_dump().items()}
    ac = {"chain_mail": 16, "leather": 11 + mods["dexterity"], "none": 10 + mods["dexterity"]}[data.equipment.armor]
    ac += 2 if data.equipment.shield else 0
    ac += 1 if data.fighting_style == "defense" and data.equipment.armor != "none" else 0
    bonus = mods["strength"] + (2 if data.fighting_style == "dueling" else 0)
    return {
        "ability_modifiers": mods, "proficiency_bonus": 2,
        "max_hp": 10 + mods["constitution"], "armor_class": ac,
        "saving_throws": {k: v + (2 if k in ("strength", "constitution") else 0) for k, v in mods.items()},
        "initiative_bonus": mods["dexterity"],
        "attacks": [AttackProfile(id="longsword", name="Espada longa (uma mão)", attack_bonus=mods["strength"]+2,
                                  damage_expression=f"1d8{bonus:+d}", damage_type="slashing").model_dump()],
    }


def resolve_attack(profile: dict, armor_class: int, randbelow: RandBelow = secrets.randbelow) -> dict:
    attack = roll("1d20", randbelow=randbelow)
    natural = attack.kept[0]
    critical = natural == 20
    hit = critical or (natural != 1 and natural + profile["attack_bonus"] >= armor_class)
    damage_roll = None
    if hit:
        expression = profile["damage_expression"]
        if critical:
            match = DICE.fullmatch(expression)
            expression = f"{int(match.group(1))*2}d{match.group(2)}{match.group(3) or ''}"
        damage_roll = roll(expression, randbelow=randbelow)
    return {"hit": hit, "critical": critical, "attack_roll": attack.model_dump(),
            "attack_bonus": profile["attack_bonus"], "attack_total": natural+profile["attack_bonus"],
            "damage_roll": damage_roll.model_dump() if damage_roll else None,
            "damage": max(0, damage_roll.total) if damage_roll else 0, "damage_type": profile["damage_type"]}


TRAINING_MONSTER = {
    "id": "training-goblin", "name": "Goblin de treino (exemplo)", "rule_set": "dnd5e-2014",
    "is_example": True, "source": "ARCANUM synthetic training fixture; not imported from a book",
    "max_hp": 7, "armor_class": 13, "dexterity_modifier": 2,
    "attacks": [AttackProfile(id="training-blade", name="Lâmina de treino", attack_bonus=4,
                              damage_expression="1d6+2", damage_type="slashing").model_dump()],
}

