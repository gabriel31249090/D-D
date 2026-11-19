"""Read local tabletop sources as data. No imported repository code runs here."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile
from contextlib import contextmanager
from zipfile import BadZipFile, ZipFile
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    title: str
    kind: str
    file: Path
    description: str
    member: str = ""

    @property
    def key(self):
        return (self.file.name, self.member, self.title)


def workspace_candidates():
    configured = os.environ.get("ARCANUM_PROJECT")
    if configured:
        yield Path(configured)
    yield Path(__file__).resolve().parents[1]
    yield Path.home() / "Downloads" / "D&D"


class Desk:
    """Private preferences, bookmarks and campaign journal in a separate store."""

    def __init__(self, data_dir):
        self.directory = Path(data_dir)
        self.directory.mkdir(exist_ok=True, parents=True)
        self.database = self.directory / "journal.sqlite3"
        self.write_script()

    def write_script(self):
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS bookmarks(source TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY,title TEXT NOT NULL,summary TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY,campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
                    title TEXT NOT NULL,kind TEXT NOT NULL,body TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            with db:
                yield db
        finally:
            db.close()

    def rows(self, sql, args=()):
        with self.connect() as db:
            return list(db.execute(sql, args))

    def change(self, sql, args):
        with self.connect() as db:
            return db.execute(sql, args).lastrowid

    def raw_path(self):
        preferred = self.rows("SELECT value FROM settings WHERE key='raw'")
        if preferred:
            return Path(preferred[0][0])
        configured = os.environ.get("ARCANUM_RAW_DIR")
        if configured:
            return Path(configured)
        return next((p for root in workspace_candidates() for p in (root/".arcanum"/"sources"/"raw", root/"raw") if p.is_dir()), None)

    def set_raw(self, path):
        self.change("INSERT OR REPLACE INTO settings VALUES ('raw',?)", (str(path),))

    def toggle_bookmark(self, entry):
        source = json.dumps(entry.key)
        with self.connect() as db:
            if not db.execute("DELETE FROM bookmarks WHERE source=?", (source,)).rowcount:
                db.execute("INSERT INTO bookmarks VALUES (?)", (source,))

    def bookmarks(self):
        return {tuple(json.loads(row[0])) for row in self.rows("SELECT source FROM bookmarks")}


def safe_member(name):
    parts = PurePosixPath(name.replace("\\", "/")).parts
    return bool(parts) and not any(p in ("/", "..") or ":" in p for p in parts)


def read_member(entry, limit):
    if not safe_member(entry.member):
        raise ValueError("O caminho do item no pacote é inválido.")
    with ZipFile(entry.file) as archive:
        info = archive.getinfo(entry.member)
        if info.file_size > limit:
            raise ValueError("O item excede o tamanho aceito.")
        with archive.open(info) as member:
            data = member.read(limit + 1)
            if len(data) > limit:
                raise ValueError("O item excede o tamanho aceito.")
            return data


REPOS = {
    "aslib-master.zip": "Editor de mapas em C++. A geração de masmorras do ARCANUM pode ser usada na área Mapas.",
    "dungeoneer-master.zip": "Mesa virtual. Os mapas de exemplo deste pacote aparecem individualmente na biblioteca.",
    "compass-master.zip": "Catálogo de recursos de RPG. A biblioteca do ARCANUM permite pesquisar por nome, filtrar por tipo e guardar favoritos.",
    "chronicler-master.zip": "Organização de cenários e notas. A área Campanhas permite registrar personagens, lugares e sessões.",
}


def catalogue(directory):
    entries, issues = [], []
    if not directory or not directory.is_dir():
        return entries, issues
    for file in sorted(directory.iterdir(), key=lambda p: p.name.casefold()):
        if not file.is_file() or file.is_symlink():
            continue
        try:
            suffix = file.suffix.casefold()
            if suffix == ".pdf":
                entries.append(Entry(file.stem, "PDF", file, "Documento local · " + f"{file.stat().st_size / 1048576:.1f} MB"))
            elif suffix == ".zip":
                with ZipFile(file) as archive:
                    names = [i.filename for i in archive.infolist() if not i.is_dir() and safe_member(i.filename)]
                explanation = REPOS.get(file.name.casefold(), "Pacote de documentos locais.")
                entries.append(Entry(file.stem, "Pacote", file, f"{explanation}\n\n{len(names)} arquivos no pacote."))
                for name in names:
                    ext = PurePosixPath(name).suffix.lower()
                    if ext in (".pdf", ".dungeoneer_map"):
                        entries.append(Entry(PurePosixPath(name).stem, "Mapa" if ext == ".dungeoneer_map" else "PDF", file, f"Origem: {file.name}\n{name}", name))
            elif file.name.casefold() == "dados_e_rolagens.json":
                if file.stat().st_size > 2_000_000:
                    raise ValueError("O JSON excede 2 MB")
                records = json.loads(file.read_text(encoding="utf-8-sig"))
                if not isinstance(records, list):
                    raise ValueError("Formato de fichas desconhecido")
                for record in records:
                    if not isinstance(record, dict): raise ValueError("Ficha inválida")
                    title = f"{record['class']} · {record['race']}"
                    lines = [f"Valebruma · Ficha {record['id']}", f"PV {record['hp']}     CA {record['ac']}", "", "Atributos registrados"]
                    lines += [f"{key}   {value}" for key, value in record["final_attributes"].items()]
                    lines.extend(["", "Rolagens de origem"])
                    for roll in record["rolls"]:
                        lines.append(f"{' + '.join(map(str, roll['dice']))}   |   descarta {roll['discard']}   →   {roll['score']}")
                    entries.append(Entry(title, "Ficha", file, "\n".join(lines)))
        except (OSError, KeyError, TypeError, ValueError, AttributeError, RuntimeError, BadZipFile) as exc:
            issues.append(f"{file.name}: {exc}")
    return entries, issues


def local_document(entry, cache):
    """Return a local PDF or the verified artwork in a Dungeoneer map."""
    if entry.kind == "PDF" and not entry.member:
        return entry.file
    data = read_member(entry, 32 * 1024**2)
    if entry.kind == "Mapa":
        foreground = json.loads(data)["foregroundBase64"]
        data = base64.b64decode(foreground, validate=True)
        if data.startswith(b"\x89PNG\r\n\x1a\n"): suffix = ".png"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP": suffix = ".webp"
        elif data.startswith(b"\xff\xd8\xff"): suffix = ".jpg"
        else: raise ValueError("Formato de imagem desconhecido")
    elif entry.kind == "PDF" and data.startswith(b"%PDF-"):
        suffix = ".pdf"
    else:
        raise ValueError("Este item não contém um documento compatível.")
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / (hashlib.sha256(data).hexdigest() + suffix)
    if not target.exists():
        fd, name = tempfile.mkstemp(dir=cache)
        try:
            with os.fdopen(fd, "wb") as out: out.write(data)
            os.replace(name, target)
        finally:
            Path(name).unlink(missing_ok=True)
    return target
