"""Native Tkinter map workbench; build_map(parent) integrates with the desktop shell."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from .map_model import MapDocument, MapHistory, MapStore, generate_map

BG = "#131923"
PANEL = "#1b2431"
TEXT = "#e9e5dc"
MUTED = "#b3bdca"
GOLD = "#e3bc73"
GRID = "#344151"
TERRAIN = {"void": "#111620", "wall": "#4a5664", "floor": "#8b806c", "door": "#b88144"}
TOOLS = {"Sala": "room", "Corredor": "corridor", "Piso": "floor", "Parede": "wall",
         "Porta": "door", "Token": "token", "Borracha": "void"}


class MapView(tk.Frame):
    def __init__(self, parent, *, data_dir: Path | str | None = None):
        super().__init__(parent, bg=BG)
        inherited = getattr(getattr(parent, "store", None), "data_dir", None)
        self.store = MapStore(data_dir if data_dir is not None else inherited)
        self.history = MapHistory(generate_map())
        self.saved_state = self.history.document.to_dict()
        self.is_persisted = False
        self.compact = None
        self.cell_size = 23
        self.start = None
        self.drag_cells = set()
        self.drag_token_id = None
        self.maps = []
        self.name = tk.StringVar(self, value=self.history.document.name)
        self.seed = tk.StringVar(self, value="Arcanum")
        self.width_value = tk.StringVar(self, value="41")
        self.height_value = tk.StringVar(self, value="29")
        self.rooms_value = tk.StringVar(self, value="8")
        self.tool = tk.StringVar(self, value="Sala")
        self.status = tk.StringVar(self)
        self.position = tk.StringVar(self, value="Arraste no mapa para desenhar uma sala.")
        self._build()
        self.bind("<Configure>", self._responsive)
        self.refresh_maps()
        if self.maps:
            self._load_document(self.store.load(self.maps[0]["id"]))
        self.redraw()

    @property
    def document(self) -> MapDocument:
        return self.history.document

    def has_unsaved_changes(self) -> bool:
        return self.document.to_dict() != self.saved_state or self.name.get().strip() != self.document.name

    def _label(self, parent, text, **options):
        options.setdefault("fg", TEXT)
        return tk.Label(parent, text=text, bg=parent.cget("bg"),
                        font=("Segoe UI", 11), **options)

    def _button(self, parent, text, command, *, accent=False, **options):
        return tk.Button(parent, text=text, command=command, bg=GOLD if accent else "#2c3848",
                         fg=BG if accent else TEXT, activebackground="#cba45f" if accent else "#3d4e63",
                         activeforeground=BG if accent else TEXT, relief="flat", bd=0,
                         padx=11, pady=7, font=("Segoe UI", 11), cursor="hand2", **options)

    def _entry(self, parent, variable, width):
        return tk.Entry(parent, textvariable=variable, width=width, bg="#101722", fg=TEXT,
                        insertbackground=GOLD, relief="flat", font=("Segoe UI", 11))

    def _build(self):
        heading = tk.Frame(self, bg=BG)
        heading.pack(fill="x", padx=18, pady=(14, 10))
        tk.Label(heading, text="Cartógrafo", bg=BG, fg=GOLD,
                 font=("Segoe UI Semibold", 22)).pack(anchor="w")
        self._label(heading, "Salas, caminhos e encontros em uma mesa local.", fg=MUTED).pack(anchor="w")
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18)
        sidebar = tk.Frame(body, bg=PANEL, width=225)
        self.sidebar = sidebar
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        self._label(sidebar, "SEUS MAPAS", anchor="w", fg=GOLD).pack(fill="x", padx=12, pady=(12, 8))
        self.saved_list = tk.Listbox(sidebar, bg=PANEL, fg=TEXT, selectbackground="#455368",
                                    selectforeground=TEXT, activestyle="none", relief="flat",
                                    width=25, font=("Segoe UI", 11), exportselection=False)
        self.saved_list.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.saved_list.bind("<Double-Button-1>", lambda event: self.open_selected())
        self.saved_list.bind("<Return>", lambda event: self.open_selected())
        self._button(sidebar, "Abrir selecionado", self.open_selected).pack(fill="x", padx=10, pady=4)
        self._button(sidebar, "Novo mapa vazio", self.new_map).pack(fill="x", padx=10, pady=(4, 12))
        work = tk.Frame(body, bg=BG)
        self.work = work
        work.pack(side="left", fill="both", expand=True)
        self.compact_library = tk.Frame(work, bg=BG)
        self._label(self.compact_library, "Mapas").pack(side="left", padx=(0, 8))
        self.map_selector = ttk.Combobox(self.compact_library, state="readonly", width=24)
        self.map_selector.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.map_selector.bind("<<ComboboxSelected>>", self._open_compact)
        self._button(self.compact_library, "Novo mapa", self.new_map).pack(side="left")
        naming = tk.Frame(work, bg=BG)
        self.naming = naming
        naming.pack(fill="x", pady=(0, 8))
        self._label(naming, "Nome").pack(side="left")
        self._entry(naming, self.name, 32).pack(side="left", fill="x", expand=True, ipady=8, padx=10)
        self._button(naming, "Salvar", self.save_current, accent=True).pack(side="left", padx=(0, 6))
        self._button(naming, "Exportar", self.export_map).pack(side="left")
        generation = tk.Frame(work, bg=PANEL, padx=10, pady=10)
        generation.pack(fill="x", pady=(0, 8))
        self.generation_groups = []
        for index, (label, variable, width) in enumerate((("Semente", self.seed, 12), ("Colunas", self.width_value, 4),
                                       ("Linhas", self.height_value, 4), ("Salas", self.rooms_value, 3))):
            group = tk.Frame(generation, bg=PANEL)
            group.grid(row=0, column=index, sticky="w", padx=(0, 10))
            self._label(group, label).pack(side="left", padx=(0, 5))
            self._entry(group, variable, width).pack(side="left", ipady=6)
            self.generation_groups.append(group)
        self.generate_button = self._button(generation, "Gerar conectada", self.generate)
        self.generate_button.grid(row=0, column=4, sticky="w")
        tools = tk.Frame(work, bg=BG)
        tools.pack(fill="x", pady=(0, 8))
        self.tool_buttons = []
        for index, label in enumerate(TOOLS):
            button = tk.Radiobutton(tools, text=label, variable=self.tool, value=label, bg=BG, fg=TEXT,
                           selectcolor="#41516a", activebackground=BG, activeforeground=GOLD,
                           indicatoron=False, relief="flat", padx=9, pady=7,
                           font=("Segoe UI", 10), command=self._tool_changed)
            button.grid(row=0, column=index, sticky="w", padx=(0, 4), pady=(0, 3))
            self.tool_buttons.append(button)
        actions = tk.Frame(work, bg=BG)
        actions.pack(fill="x", pady=(0, 7))
        self.undo_button = self._button(actions, "Desfazer", self.undo)
        self.undo_button.pack(side="left", padx=(0, 5))
        self.redo_button = self._button(actions, "Refazer", self.redo)
        self.redo_button.pack(side="left", padx=(0, 15))
        self._label(actions, "Zoom").pack(side="left")
        tk.Scale(actions, from_=14, to=38, orient="horizontal", showvalue=False, length=150,
                 bg=BG, fg=TEXT, troughcolor=PANEL, highlightthickness=0,
                 command=self._zoom, variable=tk.IntVar(self, value=self.cell_size)).pack(side="left")
        area = tk.Frame(work, bg=BG)
        area.pack(fill="both", expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(area, bg=TERRAIN["void"], highlightthickness=1,
                                highlightbackground=GRID, width=730, height=440)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Button-3>", self._erase_token)
        self.canvas.bind("<Motion>", self._pointer)
        self.canvas.bind("<Control-z>", lambda event: self.undo())
        self.canvas.bind("<Control-y>", lambda event: self.redo())
        self.canvas.bind("<Control-s>", lambda event: self.save_current())
        self.canvas.bind("<ButtonPress-2>", lambda event: self.canvas.scan_mark(event.x, event.y))
        self.canvas.bind("<B2-Motion>", lambda event: self.canvas.scan_dragto(event.x, event.y, gain=1))
        self.canvas.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units"))
        tk.Label(work, textvariable=self.position, bg=BG, fg=MUTED, anchor="w",
                 font=("Segoe UI", 10)).pack(fill="x", pady=(6, 2))
        tk.Label(self, textvariable=self.status, bg=BG, fg=GOLD, anchor="w",
                 font=("Segoe UI", 11)).pack(fill="x", padx=18, pady=(6, 12))

    def _responsive(self, event):
        if event.widget is not self:
            return
        compact = event.width < 1050
        if compact == self.compact:
            return
        self.compact = compact
        if compact:
            self.sidebar.pack_forget()
            self.compact_library.pack(fill="x", pady=(0, 8), before=self.naming)
        else:
            self.compact_library.pack_forget()
            self.sidebar.pack(side="left", fill="y", padx=(0, 12), before=self.work)
        columns = 2 if compact else 4
        for index, group in enumerate(self.generation_groups):
            group.grid_configure(row=index // columns, column=index % columns, pady=(0, 5))
        self.generate_button.grid_configure(row=2 if compact else 0, column=0 if compact else 4,
                                            columnspan=2 if compact else 1)
        columns = 4 if compact else 8
        for index, button in enumerate(self.tool_buttons):
            button.grid_configure(row=index // columns, column=index % columns)

    def _open_compact(self, event=None):
        index = self.map_selector.current()
        if index >= 0:
            self.saved_list.selection_clear(0, "end")
            self.saved_list.selection_set(index)
            self.open_selected()

    def _tool_changed(self):
        help_text = {"Sala": "Arraste uma área de pelo menos 3 × 3 células para criar paredes e piso.",
                     "Corredor": "Arraste entre dois pontos para abrir um corredor em L.",
                     "Token": "Clique no piso para nomear um token; arraste um token para movê-lo. Botão direito remove."}
        self.position.set(help_text.get(self.tool.get(), "Clique e arraste para pintar. Cada traço pode ser desfeito."))

    def _coordinates(self, event):
        x = int(self.canvas.canvasx(event.x) // self.cell_size)
        y = int(self.canvas.canvasy(event.y) // self.cell_size)
        return (x, y) if self.document.inside(x, y) else None

    def _pointer(self, event):
        cell = self._coordinates(event)
        if cell:
            token = next((item for item in self.document.tokens if (item["x"], item["y"]) == cell), None)
            token_name = f"  |  {token['label']}" if token else ""
            self.position.set(f"Coluna {cell[0] + 1} · linha {cell[1] + 1}{token_name}  |  {self.tool.get()}  |  Botão do meio: mover a vista")

    def _press(self, event):
        self.canvas.focus_set()
        self.start = self._coordinates(event)
        self.last_drag = self.start
        self.drag_cells = {self.start} if self.start else set()
        self.drag_token_id = None
        if self.start and self.tool.get() == "Token":
            token = next((item for item in self.document.tokens if (item["x"], item["y"]) == self.start), None)
            if token:
                self.drag_token_id = token["id"]
        self._drag(event)

    def _drag(self, event):
        end = self._coordinates(event)
        if not self.start or not end:
            return
        self.canvas.delete("preview")
        if self.tool.get() in ("Sala", "Corredor", "Token"):
            x1, y1 = self.start
            x2, y2 = end
            self.canvas.create_rectangle(min(x1, x2) * self.cell_size, min(y1, y2) * self.cell_size,
                (max(x1, x2) + 1) * self.cell_size, (max(y1, y2) + 1) * self.cell_size,
                outline=GOLD, width=2, dash=(5, 3), tags="preview")
        else:
            previous = self.last_drag or end
            steps = max(abs(end[0] - previous[0]), abs(end[1] - previous[1]), 1)
            for step in range(steps + 1):
                self.drag_cells.add((round(previous[0] + (end[0] - previous[0]) * step / steps),
                                     round(previous[1] + (end[1] - previous[1]) * step / steps)))
            self.last_drag = end
            color = TERRAIN[TOOLS[self.tool.get()]]
            for x, y in self.drag_cells:
                self.canvas.create_rectangle(x * self.cell_size, y * self.cell_size,
                    (x + 1) * self.cell_size, (y + 1) * self.cell_size,
                    fill=color, outline=GOLD, tags="preview")

    def _release(self, event):
        end = self._coordinates(event)
        start = self.start
        self.start = None
        self.canvas.delete("preview")
        if not start or not end:
            return
        try:
            if self.tool.get() == "Sala":
                self.history.room(start, end)
            elif self.tool.get() == "Corredor":
                self.history.corridor(start, end)
            elif self.tool.get() == "Token":
                if self.drag_token_id:
                    self.history.token(*end, token_id=self.drag_token_id)
                else:
                    label = simpledialog.askstring("Adicionar token", "Nome do token (até 24 caracteres):",
                                                   initialvalue="Aventureiro", parent=self)
                    if label is not None:
                        self.history.token(*end, label=label)
            else:
                self.drag_cells.add(end)
                self.history.paint(self.drag_cells, TOOLS[self.tool.get()])
            self.redraw()
        except ValueError as error:
            messagebox.showinfo("Editar mapa", str(error), parent=self)

    def _erase_token(self, event):
        cell = self._coordinates(event)
        if cell:
            self.history.remove_token(*cell)
            self.redraw()

    def _zoom(self, value):
        self.cell_size = int(float(value))
        if hasattr(self, "canvas"):
            self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        size = self.cell_size
        for y, row in enumerate(self.document.cells):
            for x, tile in enumerate(row):
                self.canvas.create_rectangle(x * size, y * size, (x + 1) * size, (y + 1) * size,
                                             fill=TERRAIN[tile], outline=GRID, width=1)
                if tile == "door":
                    self.canvas.create_line(x * size + 4, y * size + size // 2,
                                            (x + 1) * size - 4, y * size + size // 2, fill="#f1d6a0", width=3)
        for token in self.document.tokens:
            x, y = token["x"] * size, token["y"] * size
            self.canvas.create_oval(x + 3, y + 3, x + size - 3, y + size - 3,
                                    fill=token["color"], outline="#101722", width=2)
            self.canvas.create_text(x + size / 2, y + size / 2, text=token["label"][:1].upper(),
                                    fill=BG, font=("Segoe UI Semibold", max(9, size // 2)))
        self.canvas.configure(scrollregion=(0, 0, self.document.width * size, self.document.height * size))
        self.undo_button.configure(state="normal" if self.history.can_undo else "disabled")
        self.redo_button.configure(state="normal" if self.history.can_redo else "disabled")
        connectivity = "passagens conectadas" if self.document.connected() else "sem piso ou com áreas separadas"
        dirty = ("Alterações por salvar" if self.has_unsaved_changes() else
                 "Salvo neste computador" if self.is_persisted else "Pronto para editar · ainda não salvo")
        self.status.set(f"{self.document.width} × {self.document.height} · {len(self.document.tokens)} tokens · {connectivity} · {dirty}")

    def undo(self):
        if self.history.undo():
            self._sync_fields()
        self.redraw()

    def redo(self):
        if self.history.redo():
            self._sync_fields()
        self.redraw()

    def _sync_fields(self):
        self.name.set(self.document.name)
        self.width_value.set(str(self.document.width))
        self.height_value.set(str(self.document.height))
        self.seed.set(self.document.seed or "Arcanum")

    def _discard_allowed(self):
        if not self.has_unsaved_changes():
            return True
        answer = messagebox.askyesnocancel("Mapa com alterações", "Salvar o mapa atual antes de continuar?", parent=self)
        return False if answer is None else (self.save_current() if answer else True)

    def _dimensions(self):
        try:
            return int(self.width_value.get()), int(self.height_value.get())
        except ValueError as error:
            raise ValueError("Informe números inteiros em Colunas e Linhas.") from error

    def new_map(self):
        if not self._discard_allowed():
            return
        try:
            width, height = self._dimensions()
            self.history = MapHistory(MapDocument(width=width, height=height))
            self.saved_state = self.document.to_dict()
            self.is_persisted = False
            self._sync_fields()
            self.redraw()
        except ValueError as error:
            messagebox.showerror("Criar mapa", str(error), parent=self)

    def generate(self):
        try:
            width, height = self._dimensions()
            document = generate_map(width, height, self.seed.get(), int(self.rooms_value.get()), self.name.get().strip())
            self.history.replace(document)
            self._sync_fields()
            self.redraw()
        except ValueError as error:
            messagebox.showerror("Gerar masmorra", str(error), parent=self)

    def save_current(self) -> bool:
        try:
            self.history.rename(self.name.get())
            self.store.save(self.document)
            self.saved_state = self.document.to_dict()
            self.is_persisted = True
            self.refresh_maps()
            self.redraw()
            return True
        except (ValueError, OSError) as error:
            messagebox.showerror("Salvar mapa", str(error), parent=self)
            return False

    def refresh_maps(self):
        self.maps = self.store.list_maps()
        self.map_selector.configure(values=[record["name"] for record in self.maps])
        self.saved_list.delete(0, "end")
        for index, record in enumerate(self.maps):
            self.saved_list.insert("end", f"{record['name']}  ·  {record['width']}×{record['height']}")
            if record["id"] == self.document.id:
                self.saved_list.selection_set(index)
                self.map_selector.current(index)

    def _load_document(self, document):
        self.history = MapHistory(document)
        self.saved_state = document.to_dict()
        self.is_persisted = True
        self._sync_fields()

    def open_selected(self):
        selection = self.saved_list.curselection()
        if not selection:
            self.status.set("Selecione um mapa na lista para abrir.")
            return
        selected_id = self.maps[selection[0]]["id"]
        if not self._discard_allowed():
            return
        try:
            self._load_document(self.store.load(selected_id))
            self.redraw()
        except (OSError, ValueError) as error:
            messagebox.showerror("Abrir mapa", str(error), parent=self)

    def export_map(self):
        try:
            self.history.rename(self.name.get())
            filename = filedialog.asksaveasfilename(parent=self, title="Exportar mapa ARCANUM",
                initialfile="mapa-arcanum.json", defaultextension=".json", filetypes=[("Mapa JSON", "*.json")])
            if filename:
                self.store.export(self.document, filename)
                self.redraw()
                self.status.set("JSON exportado. O mapa também pode ser salvo na biblioteca deste computador.")
        except (OSError, ValueError) as error:
            messagebox.showerror("Exportar mapa", str(error), parent=self)


def build_map(parent) -> MapView:
    """Build and pack the native editor. Uses parent.store.data_dir when present."""
    widget = MapView(parent)
    widget.pack(fill="both", expand=True)
    return widget
