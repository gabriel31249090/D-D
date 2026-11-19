import pytest
from hypothesis import given, strategies as st
from backend.rules import character_stats, modifier, proficiency, resolve_attack, roll
from backend.schemas import CharacterCreate


def sequence_rng(values):
    iterator = iter(values)
    def randbelow(sides):
        value = next(iterator)
        assert 1 <= value <= sides
        return value - 1
    return randbelow


@given(st.integers(min_value=3, max_value=20))
def test_modifier_rounds_down(score):
    value = modifier(score)
    assert 2*value <= score-10 < 2*(value+1)


@pytest.mark.parametrize("level,expected", [(1,2),(4,2),(5,3),(8,3),(9,4),(13,5),(17,6),(20,6)])
def test_proficiency_tiers(level, expected):
    assert proficiency(level) == expected


def test_first_level_hp_armor_and_saves():
    data = CharacterCreate(name="Aria", abilities={"strength":16,"constitution":16})
    stats = character_stats(data)
    assert stats["max_hp"] == 13
    assert stats["armor_class"] == 19  # chain 16 + shield 2 + defense 1
    assert stats["saving_throws"]["constitution"] == 5
    assert stats["attacks"][0]["attack_bonus"] == 5
    assert stats["attacks"][0]["damage_expression"] == "1d8+3"


def test_unarmored_defense_does_not_add_ac_and_negative_dex_applies():
    data = CharacterCreate(name="Aria", equipment={"armor":"none","shield":False}, abilities={"dexterity":8})
    assert character_stats(data)["armor_class"] == 9
    data = CharacterCreate(name="Aria", equipment={"armor":"leather","shield":True}, abilities={"dexterity":8})
    assert character_stats(data)["armor_class"] == 13


def test_dueling_with_shield_adds_damage_only():
    stats = character_stats(CharacterCreate(name="Aria", fighting_style="dueling", abilities={"strength":16}))
    assert stats["armor_class"] == 18
    assert stats["attacks"][0]["damage_expression"] == "1d8+5"


def test_critical_doubles_dice_not_modifier():
    profile = {"attack_bonus":5,"damage_expression":"1d8+3","damage_type":"slashing"}
    outcome = resolve_attack(profile, 999, sequence_rng([20, 4, 5]))
    assert outcome["hit"] and outcome["critical"]
    assert outcome["damage"] == 12
    assert outcome["damage_roll"]["rolls"] == [4, 5]


def test_natural_one_always_misses_and_equality_hits():
    profile = {"attack_bonus":50,"damage_expression":"1d8+3","damage_type":"slashing"}
    outcome = resolve_attack(profile, 2, sequence_rng([1]))
    assert not outcome["hit"] and outcome["damage"] == 0
    assert outcome["damage_roll"] is None
    profile["attack_bonus"] = 5
    assert resolve_attack(profile, 15, sequence_rng([10, 1]))["hit"]


@pytest.mark.parametrize("mode,total", [("advantage",20),("disadvantage",2)])
def test_advantage_uses_two_d20_and_keeps_one(mode, total):
    result = roll("1d20+1", mode, sequence_rng([1,19]))
    assert result.rolls == [1,19]
    assert result.total == total


@pytest.mark.parametrize("expression", ["__import__('os')", "1d0", "0d6", "51d6", "1d20+1001", "1d6;1d6", "1d6\n", "1d99999999"])
def test_invalid_dice_expressions_are_rejected(expression):
    with pytest.raises(ValueError):
        roll(expression)


def test_dice_limits_and_negative_damage_floor():
    result = roll("50d4-1000", randbelow=lambda n: 0)
    assert len(result.rolls) == 50 and result.total == -950
    with pytest.raises(ValueError):
        roll("2d20", "advantage")
    profile = {"attack_bonus":5,"damage_expression":"1d8-5","damage_type":"slashing"}
    assert resolve_attack(profile, 5, sequence_rng([10,1]))["damage"] == 0

