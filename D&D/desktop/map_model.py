"""Local map documents, bounded editing and deterministic connected generation.

The two-cell corridor carving technique was inspected in the user's raw archive
``AsLib-master.zip``, member ``AsLib-master/aslib/AsMaze.hpp`` (mazeDig/mazeMake),
by Kasugaccho / As Project, marked CC0 1.0 Universal. The generator below is a
new iterative Python implementation of that technique, with connected rooms.
No third-party images, executable code or other archive resources are bundled.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import re
import tempfile
from typing import Callable, Iterable
from uuid import uuid4

TILES = frozenset({"void", "wall", "floor", "door"})
WALKABLE = frozenset({"floor", "door"})
ID = re.compile(r"[0-9a-f]{32}", re.ASCII)
FORMAT = "arcanum-map-v1"
MAX_FILE_BYTES = 1_000_000
TOKEN_COLORS = ("#e3bc73", "#7ec8bd", "#cb8d92", "#a4b8ed")


def data_directory() -> Path:
    configured = os.environ.get("ARCANUM_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    local = os.environ.get("LOCALAPPDATA")
    return (Path(local) if local else Path.home() / "AppData" / "Local") / "Arcanum"


def _integer(value, minimum: int, maximum: int, label: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{label}: informe um inteiro entre {minimum} e {maximum}.")
    return value


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("Identificador de mapa inválido.")
    return value


@dataclass
class MapDocument:
    name: str = "Nova masmorra"
    width: int = 41
    height: int = 29
    id: str = field(default_factory=lambda: uuid4().hex)
    cells: list[list[str]] = field(default_factory=list)
    tokens: list[dict] = field(default_factory=list)
    seed: str = ""
    generator: str = "manual"

    def __post_init__(self):
        _integer(self.width, 9, 101, "Largura")
        _integer(self.height, 9, 81, "Altura")
        if not self.cells:
            self.cells = [["void"] * self.width for _ in range(self.height)]
        self.validate()

    def validate(self) -> None:
        _identifier(self.id)
        _integer(self.width, 9, 101, "Largura")
        _integer(self.height, 9, 81, "Altura")
        if not isinstance(self.name, str) or not self.name.strip() or len(self.name) > 100:
            raise ValueError("O nome do mapa deve ter de 1 a 100 caracteres.")
        if not isinstance(self.seed, str) or len(self.seed) > 80:
            raise ValueError("A semente deve ter até 80 caracteres.")
        if self.generator not in ("manual", "connected-maze-v1"):
            raise ValueError("Gerador de mapa desconhecido.")
        if not isinstance(self.cells, list) or len(self.cells) != self.height:
            raise ValueError("Grade incompatível com a altura do mapa.")
        if any(not isinstance(row, list) or len(row) != self.width
               or any(not isinstance(tile, str) or tile not in TILES for tile in row) for row in self.cells):
            raise ValueError("A grade contém tamanho ou tipo de terreno inválido.")
        if not isinstance(self.tokens, list) or len(self.tokens) > 100:
            raise ValueError("Um mapa aceita até 100 tokens.")
        seen = set()
        token_ids = set()
        for token in self.tokens:
            if not isinstance(token, dict) or set(token) != {"id", "x", "y", "label", "color"}:
                raise ValueError("Estrutura de token inválida.")
            _identifier(token["id"])
            x = _integer(token["x"], 0, self.width - 1, "Coluna do token")
            y = _integer(token["y"], 0, self.height - 1, "Linha do token")
            if self.cells[y][x] not in WALKABLE:
                raise ValueError("Tokens precisam estar sobre piso ou porta.")
            if (x, y) in seen or token["id"] in token_ids:
                raise ValueError("Há tokens duplicados na mesma posição.")
            seen.add((x, y))
            token_ids.add(token["id"])
            if not isinstance(token["label"], str) or not token["label"].strip() or len(token["label"]) > 24:
                raise ValueError("O nome do token deve ter de 1 a 24 caracteres.")
            if token["color"] not in TOKEN_COLORS:
                raise ValueError("Cor de token inválida.")

    def inside(self, x: int, y: int) -> bool:
        return type(x) is int and type(y) is int and 0 <= x < self.width and 0 <= y < self.height

    def to_dict(self) -> dict:
        self.validate()
        return {"format": FORMAT, "id": self.id, "name": self.name, "width": self.width,
                "height": self.height, "cells": deepcopy(self.cells), "tokens": deepcopy(self.tokens),
                "seed": self.seed, "generator": self.generator}

    @classmethod
    def from_dict(cls, payload: dict) -> "MapDocument":
        keys = {"format", "id", "name", "width", "height", "cells", "tokens", "seed", "generator"}
        if not isinstance(payload, dict) or set(payload) != keys or payload.get("format") != FORMAT:
            raise ValueError("Este arquivo não é um mapa ARCANUM compatível.")
        if not isinstance(payload["cells"], list) or not payload["cells"]:
            raise ValueError("O arquivo não contém uma grade válida.")
        return cls(**deepcopy({k: v for k, v in payload.items() if k != "format"}))

    def connected(self) -> bool:
        accessible = {(x, y) for y, row in enumerate(self.cells) for x, tile in enumerate(row) if tile in WALKABLE}
        if not accessible:
            return False
        start = min(accessible)
        reached = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for candidate in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if candidate in accessible and candidate not in reached:
                    reached.add(candidate)
                    queue.append(candidate)
        return reached == accessible


def generate_map(width: int = 41, height: int = 29, seed: str = "Arcanum",
                 rooms: int = 8, name: str = "Masmorra gerada") -> MapDocument:
    """Carve a connected maze in two-cell steps, then widen connected rooms.

    Conceptual source: AsLib AsMaze.hpp mazeDig/mazeMake, CC0, Kasugaccho /
    As Project. Python's local Random(seed) replaces the original global RNG.
    Connectivity is preserved by attaching every room to an existing floor.
    """
    _integer(rooms, 0, 30, "Quantidade de salas")
    document = MapDocument(name=name, width=width, height=height, seed=str(seed), generator="connected-maze-v1")
    rng = random.Random(document.seed)
    cells = document.cells = [["wall"] * width for _ in range(height)]
    cells[1][1] = "floor"
    stack = [(1, 1)]
    while stack:
        x, y = stack[-1]
        options = [(x + dx, y + dy, dx // 2, dy // 2)
                   for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))
                   if 0 < x + dx < width - 1 and 0 < y + dy < height - 1
                   and cells[y + dy][x + dx] == "wall"]
        if not options:
            stack.pop()
            continue
        nx, ny, dx, dy = rng.choice(options)
        cells[y + dy][x + dx] = cells[ny][nx] = "floor"
        stack.append((nx, ny))
    anchors = [(x, y) for y in range(1, height - 1) for x in range(1, width - 1) if cells[y][x] == "floor"]
    for _ in range(rooms):
        cx, cy = rng.choice(anchors)
        half_width, half_height = rng.randint(1, 3), rng.randint(1, 2)
        for y in range(max(1, cy - half_height), min(height - 1, cy + half_height + 1)):
            for x in range(max(1, cx - half_width), min(width - 1, cx + half_width + 1)):
                cells[y][x] = "floor"
    # Two visible entry markers inside the boundary; no isolated open cell.
    cells[1][1] = "door"
    end = max((x, y) for y, row in enumerate(cells) for x, tile in enumerate(row) if tile == "floor")
    cells[end[1]][end[0]] = "door"
    document.validate()
    return document


class MapHistory:
    """Undo/redo whole editing gestures, bounded to the latest 80 operations."""
    def __init__(self, document: MapDocument):
        self.document = document
        self._undo: list[dict] = []
        self._redo: list[dict] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def change(self, operation: Callable[[MapDocument], None]) -> bool:
        before = self.document.to_dict()
        try:
            operation(self.document)
            after = self.document.to_dict()
        except Exception:
            self.document = MapDocument.from_dict(before)
            raise
        if before == after:
            return False
        self._undo.append(before)
        self._undo = self._undo[-80:]
        self._redo.clear()
        return True

    def replace(self, document: MapDocument) -> bool:
        replacement = document.to_dict()
        replacement["id"] = self.document.id
        def operation(current):
            current.__dict__.update(MapDocument.from_dict(replacement).__dict__)
        return self.change(operation)

    def paint(self, coordinates: Iterable[tuple[int, int]], tile: str) -> bool:
        if tile not in TILES:
            raise ValueError("Escolha piso, parede, porta ou borracha.")
        positions = set(coordinates)
        def operation(document):
            if any(not document.inside(x, y) for x, y in positions):
                raise ValueError("A pintura precisa ficar dentro do mapa.")
            for x, y in positions:
                document.cells[y][x] = tile
            if tile not in WALKABLE:
                document.tokens = [token for token in document.tokens if (token["x"], token["y"]) not in positions]
        return self.change(operation)

    def room(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        x1, x2 = sorted((start[0], end[0]))
        y1, y2 = sorted((start[1], end[1]))
        if x2 - x1 < 2 or y2 - y1 < 2:
            raise ValueError("Arraste uma sala de pelo menos 3 × 3 células.")
        def operation(document):
            if not document.inside(x1, y1) or not document.inside(x2, y2):
                raise ValueError("A sala precisa ficar dentro do mapa.")
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    document.cells[y][x] = "wall" if x in (x1, x2) or y in (y1, y2) else "floor"
            document.tokens = [token for token in document.tokens if document.cells[token["y"]][token["x"]] in WALKABLE]
        return self.change(operation)

    def corridor(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        x1, y1 = start
        x2, y2 = end
        return self.paint([(x, y1) for x in range(min(x1, x2), max(x1, x2) + 1)]
                          + [(x2, y) for y in range(min(y1, y2), max(y1, y2) + 1)], "floor")

    def token(self, x: int, y: int, label: str = "Aventureiro", token_id: str | None = None) -> bool:
        def operation(document):
            if not document.inside(x, y) or document.cells[y][x] not in WALKABLE:
                raise ValueError("Coloque o token sobre piso ou porta.")
            if any(token["x"] == x and token["y"] == y and token["id"] != token_id for token in document.tokens):
                raise ValueError("Já existe um token nessa célula.")
            if token_id:
                current = next((token for token in document.tokens if token["id"] == token_id), None)
                if current is None:
                    raise ValueError("Token não encontrado.")
                current.update(x=x, y=y)
            else:
                document.tokens.append({"id": uuid4().hex, "x": x, "y": y, "label": label.strip(),
                                        "color": TOKEN_COLORS[len(document.tokens) % len(TOKEN_COLORS)]})
        return self.change(operation)

    def remove_token(self, x: int, y: int) -> bool:
        return self.change(lambda document: setattr(document, "tokens", [token for token in document.tokens
                           if (token["x"], token["y"]) != (x, y)]))

    def rename(self, name: str) -> bool:
        return self.change(lambda document: setattr(document, "name", name.strip()))

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self.document.to_dict())
        self.document = MapDocument.from_dict(self._undo.pop())
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self.document.to_dict())
        self.document = MapDocument.from_dict(self._redo.pop())
        return True


class MapStore:
    """Store independent JSON maps using opaque IDs, never user titles as paths."""
    def __init__(self, data_dir: Path | str | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else data_directory()
        self.directory = self.data_dir / "maps"
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, map_id: str) -> Path:
        return self.directory / f"{_identifier(map_id)}.json"

    def save(self, document: MapDocument) -> Path:
        destination = self._path(document.id)
        self.export(document, destination)
        return destination

    @staticmethod
    def export(document: MapDocument, destination: Path | str) -> Path:
        destination = Path(destination)
        body = json.dumps(document.to_dict(), ensure_ascii=False, indent=2)
        if len(body.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValueError("O mapa excede o limite de 1 MB.")
        descriptor, temporary = tempfile.mkstemp(prefix=".map-", suffix=".tmp", dir=destination.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return destination

    def load(self, map_id: str) -> MapDocument:
        path = self._path(map_id)
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("O arquivo de mapa excede 1 MB.")
        document = MapDocument.from_dict(json.loads(path.read_text(encoding="utf-8")))
        if document.id != map_id:
            raise ValueError("O identificador interno não corresponde ao arquivo.")
        return document

    def list_maps(self) -> list[dict]:
        result = []
        for path in self.directory.glob("*.json"):
            if not ID.fullmatch(path.stem):
                continue
            try:
                document = self.load(path.stem)
                result.append({"id": document.id, "name": document.name, "width": document.width,
                               "height": document.height, "updated_at": datetime.fromtimestamp(
                                   path.stat().st_mtime, timezone.utc).isoformat()})
            except (OSError, ValueError, TypeError, RecursionError):
                continue
        return sorted(result, key=lambda item: (item["name"].casefold(), item["id"]))
