from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
import pytest
from backend.database import Base, build_engine, session_factory
from backend.main import create_app
from backend.models import Combat, CombatEvent
from backend.schemas import CombatAction
from backend.services import DomainError, act
from test_rules import sequence_rng


@pytest.fixture
def client(tmp_path):
    app = create_app(f"sqlite:///{(tmp_path/'test.sqlite3').as_posix()}", initialize_schema=True, randbelow=lambda sides: sides-1)
    with TestClient(app) as test_client:
        yield test_client


def setup_combat(client, character=None):
    response = client.post("/api/characters", json=character or {"name":"Aria", "abilities":{"strength":16,"constitution":16}})
    assert response.status_code == 201, response.text
    hero = response.json()
    response = client.post("/api/parties", json={"name":"Valebruma","character_ids":[hero["id"]]})
    assert response.status_code == 201, response.text
    party = response.json()
    response = client.post("/api/combat", json={"party_id":party["id"],"monster_ids":["training-goblin"]})
    assert response.status_code == 201, response.text
    return hero, party, response.json()


def attack_for(combat):
    actor = next(item for item in combat["combatants"] if item["id"] == combat["current_actor_id"])
    target = next(item for item in combat["combatants"] if item["team"] != actor["team"])
    return {"type":"attack","actor_id":actor["id"],"target_id":target["id"],
            "attack_id":actor["attacks"][0]["id"],"expected_version":combat["version"]}


def test_vertical_create_save_party_attack_finish_events(client):
    hero, party, combat = setup_combat(client)
    assert hero["max_hp"] == 13 and hero["armor_class"] == 19
    assert hero["scope"].startswith("level-1")
    assert client.get("/api/characters/"+hero["id"]).json()["active_combat_id"] == combat["id"]
    assert client.get("/api/monsters").json()[0]["is_example"] is True
    request = attack_for(combat)
    response = client.post(f"/api/combat/{combat['id']}/actions", json=request)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["combat"]["status"] == "completed"
    assert result["combat"]["winner"] == "party"
    event = result["events"][0]
    assert event["type"] == "attack_resolved"
    assert event["payload"]["critical"] is True
    assert event["payload"]["damage"] == 19
    assert event["payload"]["hp_before"] == 7 and event["payload"]["hp_after"] == 0
    assert client.post(f"/api/combat/{combat['id']}/actions", json=request).status_code == 409
    events = client.get(f"/api/combat/{combat['id']}/events").json()
    assert [item["sequence"] for item in events] == [1,2,3]
    assert events[0]["payload"]["snapshot"]["version"] == 1
    assert client.get(f"/api/combat/{combat['id']}/events?after_sequence=2").json() == [events[-1]]
    saved = client.get("/api/characters/"+hero["id"]).json()
    assert saved["active_combat_id"] is None
    assert client.get("/api/parties/"+party["id"]).status_code == 200


def test_actor_target_validation_rolls_back_version(client):
    _, _, combat = setup_combat(client)
    request = attack_for(combat)
    request["target_id"] = request["actor_id"]
    response = client.post(f"/api/combat/{combat['id']}/actions", json=request)
    assert response.status_code == 409
    assert client.get(f"/api/combat/{combat['id']}").json()["version"] == 1
    request["actor_id"] = "unknown"
    assert client.post(f"/api/combat/{combat['id']}/actions", json=request).status_code == 409
    assert len(client.get(f"/api/combat/{combat['id']}/events").json()) == 1


def test_character_cannot_start_two_active_combats_or_rest(client):
    hero, party, combat = setup_combat(client)
    second = client.post("/api/combat", json={"party_id":party["id"],"monster_ids":["training-goblin"]})
    assert second.status_code == 409
    assert len(client.get("/api/combat").json()) == 1
    assert client.post(f"/api/characters/{hero['id']}/rest").status_code == 409


@pytest.mark.parametrize("extra", [{"current_hp":999},{"class_id":"wizard"},{"rule_set":"dnd5e-2024"},{"level":2},{"level":True},{"abilities":{"strength":True}},{"name":"  "}])
def test_client_cannot_create_unsupported_or_overridden_characters(client, extra):
    assert client.post("/api/characters", json={"name":"Aria", **extra}).status_code == 422


def test_command_cannot_submit_official_rolls_or_damage(client):
    _, _, combat = setup_combat(client)
    for extra in ({"damage":999},{"roll":20},{"seed":1},{"expected_version":True}):
        response = client.post(f"/api/combat/{combat['id']}/actions", json={**attack_for(combat), **extra})
        assert response.status_code == 422
    assert client.get(f"/api/combat/{combat['id']}").json()["version"] == 1


def test_dice_logged_with_limits_and_local_origin(client):
    result = client.post("/api/dice/roll", json={"expression":"2d6+3"})
    assert result.status_code == 201 and result.json()["total"] == 15
    assert result.json()["id"] > 0
    assert client.post("/api/dice/roll", json={"expression":"1d6","mode":"advantage"}).status_code == 422
    assert client.post("/api/dice/roll", json={"expression":"1d20","result":20}).status_code == 422
    assert client.post("/api/characters", json={"name":"Evil"}, headers={"Origin":"https://untrusted.example"}).status_code == 403
    assert client.get("/health", headers={"Host":"untrusted.example"}).status_code == 400
    schema = client.get("/openapi.json").json()
    assert "/api/combat/{combat_id}/actions" in schema["paths"]


def test_turn_round_action_budget_and_persistence_after_restart(tmp_path):
    url = f"sqlite:///{(tmp_path/'persistent.sqlite3').as_posix()}"
    # Initiatives 20/1; first attack natural 1; enemy hits on 20 and deals 1+1+2 = 4.
    rng = sequence_rng([20,1,1,20,1,1])
    app = create_app(url, initialize_schema=True, randbelow=rng)
    with TestClient(app) as client:
        hero, _, combat = setup_combat(client)
        response = client.post(f"/api/combat/{combat['id']}/actions", json=attack_for(combat))
        combat = response.json()["combat"]
        assert combat["version"] == 2 and combat["status"] == "active"
        assert client.post(f"/api/combat/{combat['id']}/actions", json=attack_for(combat)).json()["detail"]["code"] == "action_spent"
        response = client.post(f"/api/combat/{combat['id']}/actions", json={"type":"end_turn","actor_id":combat["current_actor_id"],"expected_version":2})
        combat = response.json()["combat"]
        assert combat["round"] == 1 and combat["version"] == 3
        combat = client.post(f"/api/combat/{combat['id']}/actions", json=attack_for(combat)).json()["combat"]
        assert client.get(f"/api/characters/{hero['id']}").json()["current_hp"] == 9
        combat = client.post(f"/api/combat/{combat['id']}/actions", json={"type":"end_turn","actor_id":combat["current_actor_id"],"expected_version":4}).json()["combat"]
        assert combat["round"] == 2 and combat["version"] == 5
    with TestClient(create_app(url)) as restarted:
        assert restarted.get(f"/api/combat/{combat['id']}").json() == combat
        assert restarted.get(f"/api/characters/{hero['id']}").json()["current_hp"] == 9
        assert len(restarted.get(f"/api/combat/{combat['id']}/events").json()) == 5


def test_real_two_connection_compare_version_allows_one_command(tmp_path):
    url = f"sqlite:///{(tmp_path/'concurrent.sqlite3').as_posix()}"
    with TestClient(create_app(url, initialize_schema=True, randbelow=lambda sides: sides-1)) as client:
        _, _, combat = setup_combat(client)
    engine = build_engine(url)
    sessions = session_factory(engine)
    barrier = threading.Barrier(2)
    request = CombatAction(type="end_turn", actor_id=combat["current_actor_id"], expected_version=1)
    def worker():
        with sessions() as db:
            barrier.wait(timeout=5)
            try:
                result = act(db, combat["id"], request)
                db.commit()
                return result["combat"]["version"]
            except DomainError as error:
                db.rollback()
                return error.code
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _: worker(), range(2)))
        assert sorted(outcomes, key=str) == [2, "stale_combat"]
        with sessions() as db:
            assert db.get(Combat, combat["id"]).version == 2
            assert db.scalar(select(func.count()).select_from(CombatEvent)) == 2
    finally:
        engine.dispose()


def test_training_defeat_persists_zero_hp_releases_character_and_allows_recovery(tmp_path):
    url = f"sqlite:///{(tmp_path/'defeat.sqlite3').as_posix()}"
    # Enemy wins initiative and a critical deals fourteen against thirteen HP.
    app = create_app(url, initialize_schema=True, randbelow=sequence_rng([1,20,20,6,6]))
    with TestClient(app) as client:
        hero, party, combat = setup_combat(client)
        response = client.post(f"/api/combat/{combat['id']}/actions", json=attack_for(combat))
        assert response.status_code == 200, response.text
        combat = response.json()["combat"]
        assert combat["status"] == "completed" and combat["winner"] == "enemy"
        saved = client.get(f"/api/characters/{hero['id']}").json()
        assert saved["current_hp"] == 0 and saved["active_combat_id"] is None
        assert client.post("/api/combat", json={"party_id":party["id"],"monster_ids":["training-goblin"]}).status_code == 409
        restored = client.post(f"/api/characters/{hero['id']}/rest").json()
        assert restored["current_hp"] == restored["max_hp"] == 13


def test_alembic_upgrade_is_repeatable_and_preserves_data(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path/'migrations.sqlite3').as_posix()}"
    monkeypatch.setenv("ARCANUM_DATABASE_URL", url)
    cfg = Config(str(Path(__file__).resolve().parents[1]/"alembic.ini"))
    command.upgrade(cfg, "head")
    with TestClient(create_app(url)) as client:
        hero = client.post("/api/characters", json={"name":"Migration keeper"}).json()
    command.upgrade(cfg, "head")
    with TestClient(create_app(url)) as client:
        assert client.get(f"/api/characters/{hero['id']}").json()["name"] == "Migration keeper"
        actual = inspect(client.app.state.engine)
        assert set(Base.metadata.tables).issubset(actual.get_table_names())
        for table in Base.metadata.tables.values():
            assert {column.name for column in table.columns} == {column["name"] for column in actual.get_columns(table.name)}

