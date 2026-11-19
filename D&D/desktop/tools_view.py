"""Search the private library and keep a campaign journal."""
import os
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from zipfile import BadZipFile

from .source_data import Desk, catalogue, local_document
from .style import button, heading, scroll_list, text_area


def display(w, text):
    w.configure(state="normal")
    w.delete("1.0", "end")
    w.insert("1.0", text)
    w.configure(state="disabled")


def detail_text(parent, height=8):
    frame = ttk.Frame(parent)
    field = text_area(frame, height)
    scrollbar = ttk.Scrollbar(frame, command=field.yview)
    field.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    field.pack(side="left", fill="both", expand=True)
    return frame, field


def build_library(parent):
    desk = Desk(parent.store.data_dir)
    heading(parent, "Biblioteca", "Consulte livros, mapas, fichas e pacotes da sua pasta de fontes.")
    bar = ttk.Frame(parent)
    bar.pack(fill="x", pady=(0, 12))
    query, category, only, status = tk.StringVar(), tk.StringVar(value="Todos"), tk.BooleanVar(), tk.StringVar()
    ttk.Label(bar, text="Buscar").pack(side="left", padx=(0, 8))
    ttk.Entry(bar, textvariable=query, width=18).pack(side="left", fill="x", expand=True)
    ttk.Combobox(bar, textvariable=category, values=("Todos", "PDF", "Ficha", "Mapa", "Pacote"),
                 width=10, state="readonly").pack(side="left", padx=8)
    ttk.Checkbutton(bar, text="Favoritos", variable=only).pack(side="left")
    ttk.Label(parent, textvariable=status, style="Muted.TLabel").pack(anchor="w", pady=(0, 12))

    split = ttk.Panedwindow(parent, orient="horizontal")
    split.pack(fill="both", expand=True)
    left, listing = scroll_list(split, height=10)
    split.add(left, weight=2)
    right = ttk.Frame(split, padding=(15, 0, 0, 0))
    split.add(right, weight=3)
    title = tk.StringVar(value="Selecione um item")
    selected_title = ttk.Label(right, textvariable=title, style="Section.TLabel", justify="left")
    selected_title.pack(fill="x", pady=(0, 12))
    selected_title.bind("<Configure>", lambda e: selected_title.configure(wraplength=e.width))
    content, description = detail_text(right)
    content.pack(fill="both", expand=True)
    controls = ttk.Frame(right)
    controls.pack(fill="x", pady=(12, 0))
    entries, visible = [], []
    fav = set()

    def current():
        selection = listing.curselection()
        return visible[selection[0]] if selection and selection[0] < len(visible) else None

    def show(_=None):
        entry = current()
        title.set(entry.title if entry else "Selecione um item")
        display(description, entry.description if entry else "Selecione um item da lista para ler seus detalhes.")
        opener.configure(state="normal" if entry and entry.kind in ("Mapa", "PDF") else "disabled")
        star.configure(state="normal" if entry else "disabled",
                       text="Remover favorito" if entry and entry.key in fav else "Favoritar")

    def filter_items(*_):
        item = current()
        visible[:] = [e for e in entries if (category.get() in ("Todos", e.kind))
                      and (not only.get() or e.key in fav)
                      and query.get().casefold().strip() in e.title.casefold()]
        listing.delete(0, "end")
        for entry in visible:
            listing.insert("end", f"{entry.kind}  ·  {entry.title}")
        if visible:
            index = visible.index(item) if item in visible else 0
            listing.selection_set(index)
            listing.see(index)
        show()

    def rescan():
        nonlocal fav
        raw = desk.raw_path()
        records, issues = catalogue(raw)
        entries[:] = records
        fav = desk.bookmarks()
        status.set(f"{len(entries)} itens na pasta {raw.name}" if raw and raw.is_dir() else
                   "Escolha a pasta raw para carregar as fontes.")
        filter_items()
        if issues:
            messagebox.showwarning("Fontes com erro", "\n".join(issues[:10]), parent=parent)

    def choose():
        path = filedialog.askdirectory(parent=parent, title="Escolher pasta raw", mustexist=True)
        if path:
            desk.set_raw(Path(path))
            rescan()

    def open_document():
        entry = current()
        if not entry:
            return
        try:
            os.startfile(local_document(entry, desk.directory / "preview"))
        except (OSError, ValueError, KeyError, BadZipFile) as error:
            messagebox.showerror("Não foi possível abrir", str(error), parent=parent)

    def toggle():
        nonlocal fav
        if entry := current():
            desk.toggle_bookmark(entry)
            fav = desk.bookmarks()
            filter_items()

    opener = button(controls, "Abrir arquivo", open_document, True)
    opener.pack(side="left")
    star = button(controls, "Favoritar", toggle)
    star.pack(side="left", padx=8)
    button(bar, "Escolher pasta", choose).pack(side="left", padx=(10, 0))
    listing.bind("<<ListboxSelect>>", show)
    listing.bind("<Double-Button-1>", lambda _: open_document() if current() and current().kind in ("Mapa", "PDF") else None)
    for variable in (query, category, only):
        variable.trace_add("write", filter_items)
    rescan()


def build_campaigns(parent):
    desk = Desk(parent.store.data_dir)
    heading(parent, "Campanhas", "Organize o cenário em anotações de sessão, lugares, personagens e missões.")
    split = ttk.Panedwindow(parent, orient="horizontal")
    split.pack(fill="both", expand=True)
    left, right = ttk.Frame(split), ttk.Frame(split, padding=(18, 0, 0, 0))
    split.add(left, weight=2)
    split.add(right, weight=3)
    ttk.Label(left, text="Campanhas", style="Section.TLabel").pack(anchor="w")
    campaigns_box, campaigns_list = scroll_list(left, height=4)
    campaigns_box.pack(fill="x", pady=8)
    ttk.Label(left, text="Anotações", style="Section.TLabel").pack(anchor="w", pady=(10, 0))
    notes_box, notes_list = scroll_list(left, height=5)
    notes_box.pack(fill="both", expand=True, pady=8)
    name, kind = tk.StringVar(), tk.StringVar(value="Sessão")
    ttk.Label(right, text="Título").pack(anchor="w")
    ttk.Entry(right, textvariable=name).pack(fill="x", pady=(4, 10))
    ttk.Label(right, text="Tipo de anotação").pack(anchor="w")
    ttk.Combobox(right, textvariable=kind, values=("Sessão", "Lugar", "Personagem", "Missão", "Nota"),
                 state="readonly").pack(fill="x", pady=(4, 10))
    ttk.Label(right, text="Conteúdo").pack(anchor="w")
    field, body = detail_text(right, 6)
    field.pack(fill="both", expand=True, pady=(4, 10))
    tools = ttk.Frame(right)
    tools.pack(fill="x")
    hint = tk.StringVar(value="Crie ou selecione uma campanha.")
    ttk.Label(right, textvariable=hint, style="Muted.TLabel").pack(anchor="w", pady=(8, 0))
    campaigns, notes = [], []
    active_note = None
    active_campaign = None
    original = ("", "Sessão", "")

    def values():
        return name.get(), kind.get(), body.get("1.0", "end-1c")

    def set_fields(title="", category="Sessão", text=""):
        nonlocal original
        name.set(title)
        kind.set(category)
        body.delete("1.0", "end")
        body.insert("1.0", text)
        original = values()

    def load_notes():
        notes[:] = desk.rows("SELECT * FROM notes WHERE campaign_id=? ORDER BY id DESC", (active_campaign,))
        notes_list.delete(0, "end")
        for note in notes:
            notes_list.insert("end", f"{note['kind']}  ·  {note['title']}")

    def select_campaign(_=None):
        nonlocal active_campaign, active_note
        selection = campaigns_list.curselection()
        if not selection:
            return
        requested = campaigns[selection[0]]["id"]
        if requested == active_campaign:
            return
        if not leave_note():
            campaigns_list.selection_clear(0, "end")
            for index, row in enumerate(campaigns):
                if row["id"] == active_campaign: campaigns_list.selection_set(index)
            return
        active_campaign, active_note = requested, None
        set_fields()
        load_notes()
        hint.set("Abra uma anotação ou escreva uma nova.")

    def select_note(_=None):
        nonlocal active_note
        selection = notes_list.curselection()
        if not selection:
            return
        note = notes[selection[0]]
        if note["id"] != active_note:
            if not leave_note():
                notes_list.selection_clear(0, "end")
                for index, row in enumerate(notes):
                    if row["id"] == active_note: notes_list.selection_set(index)
                return
            active_note = note["id"]
            set_fields(note["title"], note["kind"], note["body"])
            hint.set("")

    def load_campaigns(pick=None):
        campaigns[:] = desk.rows("SELECT * FROM campaigns ORDER BY id DESC")
        campaigns_list.delete(0, "end")
        for index, row in enumerate(campaigns):
            campaigns_list.insert("end", row["title"])
            if index == 0 and pick is None or row["id"] == pick:
                campaigns_list.selection_set(index)
        select_campaign()

    def new_campaign():
        from tkinter.simpledialog import askstring
        title = askstring("Nova campanha", "Nome da campanha", parent=parent)
        if title and title.strip() and leave_note():
            row = desk.change("INSERT INTO campaigns(title,summary) VALUES (?, '')", (title.strip()[:120],))
            load_campaigns(row)

    def save():
        nonlocal active_note, original
        title, category, text = values()
        title = title.strip()
        if not active_campaign or not title:
            hint.set("Selecione uma campanha e informe o título.")
            return False
        try:
            if active_note:
                desk.change("UPDATE notes SET title=?,kind=?,body=? WHERE id=?",
                            (title, category, text, active_note))
            else:
                active_note = desk.change("INSERT INTO notes(campaign_id,title,kind,body) VALUES (?,?,?,?)",
                                          (active_campaign, title, category, text))
        except sqlite3.Error as exc:
            messagebox.showerror("Erro ao salvar", str(exc), parent=parent)
            return False
        original = values()
        load_notes()
        for index, row in enumerate(notes):
            if row["id"] == active_note: notes_list.selection_set(index)
        hint.set("Anotação salva.")
        return True

    def leave_note():
        if values() == original:
            return True
        choice = messagebox.askyesnocancel("Anotação alterada", "Salvar a anotação antes de sair?", parent=parent)
        return choice is False or (choice is True and save())

    def new_note():
        nonlocal active_note
        if leave_note():
            active_note = None
            notes_list.selection_clear(0, "end")
            set_fields()
            hint.set("Escreva sua nova anotação.")

    button(left, "Nova campanha", new_campaign).pack(anchor="w", pady=(4, 0))
    button(tools, "Salvar anotação", save, True).pack(side="left")
    button(tools, "Nova anotação", new_note).pack(side="left", padx=8)
    campaigns_list.bind("<<ListboxSelect>>", select_campaign)
    notes_list.bind("<<ListboxSelect>>", select_note)
    load_campaigns()
    parent.leave_page = leave_note
