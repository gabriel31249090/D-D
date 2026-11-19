"""Meaningful local map persistence, history, connectivity and native widget checks."""
from copy import deepcopy
import json
from pathlib import Path
import tkinter as tk
from types import SimpleNamespace

import pytest

from desktop.map_model import (FORMAT, MapDocument, MapHistory, MapStore,
                               data_directory, generate_map)


@pytest.mark.parametrize("width,height", [(9, 9), (10, 10), (41, 29), (40, 28), (101, 81)])
def test_generation_is_connected_repeatable_and_bounded(width, height):
    first = generate_map(width, height, "Valebruma 2026", 12)
    second = generate_map(width, height, "Valebruma 2026", 12)
    assert first.cells == second.cells
    assert first.seed == second.seed
    assert first.connected()
    assert len(first.cells) == height and all(len(row) == width for row in first.cells)
    assert all(tile == "wall" for tile in first.cells[0] + first.cells[-1])
    assert all(row[0] == row[-1] == "wall" for row in first.cells)


def test_multiple_seeds_and_generator_validation():
    fingerprints = set()
    for seed in range(20):
        document = generate_map(21, 19, str(seed), rooms=seed % 10)
        assert document.connected()
        fingerprints.add(json.dumps(document.cells))
    assert len(fingerprints) == 20
    for args in ({"width": 10000}, {"height": True}, {"rooms": -1}, {"seed": "x" * 81}):
        with pytest.raises(ValueError):
            generate_map(**args)


def test_room_corridor_paint_token_and_atomic_history():
    history = MapHistory(MapDocument(width=15, height=13))
    history.room((1, 1), (5, 5))
    history.room((9, 6), (13, 10))
    assert not history.document.connected()
    history.corridor((3, 3), (11, 8))
    assert history.document.connected()
    history.paint([(5, 3)], "door")
    history.token(3, 3, "Mestre")
    token = deepcopy(history.document.tokens[0])
    history.token(4, 3, token_id=token["id"])
    assert history.document.tokens[0]["x"] == 4
    history.paint([(4, 3)], "wall")
    assert history.document.tokens == []
    assert history.undo()
    assert history.document.tokens[0]["id"] == token["id"]
    assert history.document.cells[3][4] == "floor"
    assert history.redo() and history.document.tokens == []
    before = history.document.to_dict()
    with pytest.raises(ValueError):
        history.paint([(2, 2), (999, 999)], "wall")
    assert history.document.to_dict() == before
    with pytest.raises(ValueError):
        history.token(0, 0)
    assert history.document.to_dict() == before
    assert history.undo()
    history.rename("Outra sala")
    assert not history.can_redo


def test_replacing_generated_map_preserves_identity_and_is_undoable():
    history = MapHistory(MapDocument(name="Meu mapa", width=13, height=11))
    original = history.document.to_dict()
    history.replace(generate_map(21, 19, "outro", name="Novo desenho"))
    assert history.document.id == original["id"]
    assert history.document.connected()
    assert history.undo() and history.document.to_dict() == original
    assert history.redo() and history.document.width == 21


def test_multiple_maps_reopen_export_and_reject_path_identifiers(tmp_path):
    store = MapStore(tmp_path)
    first = generate_map(name="Salas / nível 1")
    second = generate_map(seed="2", name="Salas / nível 1")
    store.save(first)
    store.save(second)
    assert len(store.list_maps()) == 2
    reopened = MapStore(tmp_path).load(first.id)
    assert reopened.to_dict() == first.to_dict()
    export = tmp_path / "uma cópia.json"
    store.export(reopened, export)
    assert MapDocument.from_dict(json.loads(export.read_text(encoding="utf-8"))).to_dict() == first.to_dict()
    assert not list((tmp_path / "maps").glob("*.tmp"))
    for identifier in ("../outside", "..\\outside", "C:\\Windows", "x" * 32, ""):
        with pytest.raises(ValueError):
            store.load(identifier)
    assert {item.name for item in (tmp_path / "maps").iterdir()} == {first.id + ".json", second.id + ".json"}


def test_malformed_documents_are_rejected_and_bad_local_map_does_not_hide_good_maps(tmp_path):
    store = MapStore(tmp_path)
    document = generate_map()
    store.save(document)
    payload = document.to_dict()
    payload["cells"] = []
    with pytest.raises(ValueError):
        MapDocument.from_dict(payload)
    payload = document.to_dict()
    payload["tokens"] = [{"id": "a" * 32, "x": True, "y": 1, "label": "A", "color": "#e3bc73"}]
    with pytest.raises(ValueError):
        MapDocument.from_dict(payload)
    bad_id = "b" * 32
    (store.directory / f"{bad_id}.json").write_text("{broken", encoding="utf-8")
    assert len(store.list_maps()) == 1
    mismatched = document.to_dict()
    mismatched["id"] = bad_id
    (store.directory / f"{document.id}.json").write_text(json.dumps(mismatched), encoding="utf-8")
    with pytest.raises(ValueError, match="identificador"):
        store.load(document.id)


def test_data_directory_respects_windows_profile_and_explicit_override(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.delenv("ARCANUM_DATA_DIR", raising=False)
    assert data_directory() == tmp_path / "Local" / "Arcanum"
    monkeypatch.setenv("ARCANUM_DATA_DIR", str(tmp_path / "custom"))
    assert data_directory() == tmp_path / "custom"


def test_native_editor_builds_saves_reopens_and_undoes(tmp_path):
    from desktop.map_view import build_map
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk indisponível neste ambiente: {error}")
    root.withdraw()
    root.store = SimpleNamespace(data_dir=tmp_path)
    try:
        view = build_map(root)
        root.update_idletasks()
        assert view.winfo_manager() == "pack"
        assert not view.has_unsaved_changes()
        assert "ainda não salvo" in view.status.get()
        view._responsive(SimpleNamespace(widget=view, width=580))
        assert not view.sidebar.winfo_manager()
        assert view.compact_library.winfo_manager() == "pack"
        assert view.tool_buttons[-1].grid_info()["row"] == 1
        view._responsive(SimpleNamespace(widget=view, width=1250))
        assert view.sidebar.winfo_manager() == "pack"
        assert view.tool_buttons[-1].grid_info()["row"] == 0
        assert len(view.canvas.find_all()) > 100
        view.name.set("Mapa de teste nativo")
        assert view.save_current()
        assert not view.has_unsaved_changes()
        identifier = view.document.id
        view.history.paint([(1, 1)], "wall")
        view.redraw()
        assert view.has_unsaved_changes()
        view.undo()
        assert not view.has_unsaved_changes()
        view.destroy()
        reopened = build_map(root)
        assert reopened.document.id == identifier
        assert reopened.document.name == "Mapa de teste nativo"
        assert reopened.document.connected()
    finally:
        root.destroy()


def test_native_mouse_gestures_draw_room_and_continuous_paint(tmp_path):
    from desktop.map_view import MapView
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk indisponível neste ambiente: {error}")
    root.withdraw()
    try:
        view = MapView(root, data_dir=tmp_path)
        view.history = MapHistory(MapDocument(width=15, height=13))
        view.redraw()
        size = view.cell_size
        def event(x, y):
            return SimpleNamespace(x=x * size + size // 2, y=y * size + size // 2)
        view.tool.set("Sala")
        view._press(event(1, 1))
        view._drag(event(5, 5))
        view._release(event(5, 5))
        assert view.document.cells[1][1] == "wall"
        assert view.document.cells[3][3] == "floor"
        view.tool.set("Piso")
        view._press(event(3, 3))
        view._drag(event(11, 3))
        view._release(event(11, 3))
        assert all(view.document.cells[3][x] == "floor" for x in range(3, 12))
        view.undo()
        assert view.document.cells[3][11] == "void"
        view.redo()
        assert view.document.cells[3][11] == "floor"
    finally:
        root.destroy()
