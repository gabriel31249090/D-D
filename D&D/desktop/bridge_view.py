"""Native coordination view: read-only bridge queries and explicit human sends.

No dashboard token, HTTP server, agent impersonation, or background agent launch.
The selected workspace owns its existing bridge configuration and SQLite data.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, ttk

try:
    from .style import COLORS
except ImportError:
    COLORS = {}

BG = COLORS.get("surface", "#18202c")
TEXT = COLORS.get("text", "#edf0f5")
MUTED = COLORS.get("muted", "#b1bdcc")
GOLD = COLORS.get("gold", "#d3b273")
LINE = COLORS.get("line", "#354258")
LABELS = {"human": "Usuário", "codex": "Codex", "antigravity": "Antigravity",
          "all": "Equipe", "ollama": "Ollama", "openai-compatible": "API compatível"}
STATUSES = {"pending": "Pendente", "in_progress": "Em andamento", "review": "Em revisão",
            "done": "Concluída", "blocked": "Bloqueada", "failed": "Falhou"}
LOCAL_ZONE = timezone(timedelta(hours=-4))


def readable_date(value):
    if not value:
        return "Nenhuma chamada registrada"
    try:
        return datetime.fromisoformat(value).astimezone(LOCAL_ZONE).strftime("%d/%m/%Y às %H:%M")
    except (ValueError, TypeError):
        return "Data não disponível"


def _settings(data_dir):
    path = Path(data_dir) / "desktop_settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _detect_workspace(data_dir):
    settings = _settings(data_dir)
    candidates = [os.environ.get("ARCANUM_PROJECT_DIR"), os.environ.get("ARCANUM_WORKSPACE"),
                  settings.get("bridge_workspace"), str(Path.cwd()),
                  str(Path(__file__).resolve().parents[1]), str(Path(sys.executable).parent)]
    for raw in candidates:
        if not isinstance(raw, str) or not raw.strip():
            continue
        try:
            candidate = Path(raw).expanduser().resolve()
            if (candidate / ".agent-bridge" / "bridge.sqlite3").is_file():
                return candidate
        except OSError:
            continue
    return None


def _sender_command(workspace):
    """Use only the configured ARCANUM bridge entry, never a shell command.

    Loading an arbitrary server name or a command embedded in a message is
    forbidden. The executable must be a Python interpreter and the script must
    be the existing bridge.py beside core.py and mcp_server.py.
    """
    config = workspace / ".agents" / "mcp_config.json"
    document = json.loads(config.read_text(encoding="utf-8-sig"))
    record = document["mcpServers"]["arcanum-bridge"]
    if not isinstance(record, dict) or record.get("disabled") is True:
        raise ValueError("A ponte do projeto está desabilitada.")
    arguments = record.get("args")
    if not isinstance(arguments, list) or not all(isinstance(x, str) for x in arguments):
        raise ValueError("A configuração da ponte precisa ser revisada.")
    if len(arguments) < 6 or arguments[1] != "mcp" or arguments.count("--project") != 1:
        raise ValueError("A entrada configurada não corresponde à ponte ARCANUM.")
    project_index = arguments.index("--project") + 1
    if project_index >= len(arguments) or Path(arguments[project_index]).resolve() != workspace:
        raise ValueError("A configuração aponta para outro projeto.")
    interpreter = Path(record.get("command", "")).expanduser()
    script = Path(arguments[0]).expanduser()
    if not interpreter.is_absolute() or not script.is_absolute():
        raise ValueError("A ponte precisa usar caminhos absolutos no arquivo de configuração.")
    interpreter, script = interpreter.resolve(), script.resolve()
    if interpreter.name.lower() not in ("python.exe", "pythonw.exe", "python", "python3") or not interpreter.is_file():
        raise ValueError("O Python configurado para a ponte não está disponível.")
    if script.name != "bridge.py" or not script.is_file():
        raise ValueError("O servidor ARCANUM configurado não foi encontrado.")
    if not all((script.parent / filename).is_file() for filename in ("core.py", "mcp_server.py")):
        raise ValueError("A instalação configurada da ponte está incompleta.")
    return [str(interpreter), str(script)]


def read_snapshot(workspace):
    """Read only known public coordination columns from the selected database."""
    database = (workspace / ".agent-bridge" / "bridge.sqlite3").resolve()
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=2)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        tasks = [dict(row) for row in connection.execute(
            "SELECT id,title,description,assignee,status,created_at,updated_at FROM tasks ORDER BY id DESC LIMIT 300")]
        messages = [dict(row) for row in connection.execute(
            "SELECT id,sender,recipient,task_id,body,created_at FROM messages ORDER BY id DESC LIMIT 150")]
        columns = {row[1] for row in connection.execute("PRAGMA table_info(heartbeats)")}
        heartbeat = "agent,last_seen,last_action" + (",last_tool_at" if "last_tool_at" in columns else "")
        agents = {row["agent"]: dict(row) for row in connection.execute("SELECT " + heartbeat + " FROM heartbeats")}
        return {"tasks": tasks, "messages": messages, "agents": agents}
    finally:
        connection.close()


def _scroll_text(parent, height=7):
    frame = ttk.Frame(parent)
    text = tk.Text(frame, height=height, wrap="word", font=("Segoe UI", 13), background=BG,
                   foreground=TEXT, insertbackground=TEXT, relief="flat", borderwidth=0,
                   padx=16, pady=12, selectbackground="#425472", selectforeground=TEXT)
    bar = ttk.Scrollbar(frame, command=text.yview)
    text.configure(yscrollcommand=bar.set)
    text.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    return frame, text


def _put_text(widget, content):
    current = widget.get("1.0", "end-1c")
    if current == content:
        return
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", content)
    widget.configure(state="disabled")


class BridgeView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=(0, 0, 0, 12))
        self.store = parent.store
        self.workspace = _detect_workspace(self.store.data_dir)
        self.snapshot = {"tasks": [], "messages": [], "agents": {}}
        self._sending = False
        self._destroyed = False
        self._timer = None
        self._results = queue.Queue()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Coordenação da equipe", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w")
        actions = ttk.Frame(top)
        actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=(20, 0))
        ttk.Button(actions, text="Escolher projeto", command=self.choose_workspace).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="Atualizar", command=self.refresh).pack(side="left")
        ttk.Label(top, text="Tarefas e mensagens compartilhadas com as extensões pelo MCP.",
                  font=("Segoe UI", 12), foreground=MUTED).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.notice = tk.StringVar(value="Conectando à ponte do projeto…")
        self.notice_label = ttk.Label(self, textvariable=self.notice, wraplength=850,
                                      font=("Segoe UI", 12), foreground=MUTED)
        self.notice_label.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=2, column=0, sticky="nsew")
        self.agents_page = ttk.Frame(self.tabs, padding=22)
        self.tasks_page = ttk.Frame(self.tabs, padding=20)
        self.messages_page = ttk.Frame(self.tabs, padding=20)
        self.tabs.add(self.agents_page, text="  Agentes  ")
        self.tabs.add(self.tasks_page, text="  Tarefas  ")
        self.tabs.add(self.messages_page, text="  Mensagens  ")
        self._build_agents()
        self._build_tasks()
        self._build_messages()
        self.bind("<Destroy>", self._on_destroy, add=True)
        self.bind("<Configure>", self._resize, add=True)
        self.refresh()
        self._timer = self.after(8000, self._periodic)

    def _resize(self, event):
        if event.widget is self:
            self.notice_label.configure(wraplength=max(320, event.width - 30))

    def _build_agents(self):
        self.agents_page.columnconfigure((0, 1), weight=1, uniform="agent")
        self.agent_fields = {}
        for index, key in enumerate(("codex", "antigravity")):
            panel = ttk.LabelFrame(self.agents_page, text=LABELS[key], padding=22)
            panel.grid(row=0, column=index, sticky="nsew", padx=(0, 12) if index == 0 else (12, 0))
            fields = {}
            for row, field in enumerate(("state", "last_tool", "last_action")):
                fields[field] = tk.StringVar()
                ttk.Label(panel, textvariable=fields[field], wraplength=330,
                          font=("Segoe UI", 14 if field == "state" else 12),
                          foreground=GOLD if field == "state" else TEXT).grid(row=row, column=0, sticky="w", pady=(0, 20))
            self.agent_fields[key] = fields
        ttk.Label(self.agents_page, text=(
            "Uma chamada recente confirma o uso da ponte. Um heartbeat indica apenas que um processo MCP estava em atividade.\n\n"
            "As extensões funcionam sem um executor CLI. Para verificar a conexão, peça ao próprio agente para usar bridge_health "
            "e consultar read_bridge_inbox. O envio de uma mensagem não acorda a extensão."),
            wraplength=800, justify="left", font=("Segoe UI", 13), foreground=MUTED).grid(
                row=1, column=0, columnspan=2, sticky="ew", pady=(28, 0))

    def _build_tasks(self):
        page = self.tasks_page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        page.rowconfigure(3, weight=1)
        filters = ttk.Frame(page)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        filters.columnconfigure(1, weight=1)
        ttk.Label(filters, text="Buscar tarefa").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.task_query = tk.StringVar()
        ttk.Entry(filters, textvariable=self.task_query).grid(row=0, column=1, sticky="ew", padx=(0, 18))
        self.task_status = tk.StringVar(value="Todos os status")
        ttk.Combobox(filters, textvariable=self.task_status, values=["Todos os status", *STATUSES.values()],
                     state="readonly", width=19).grid(row=0, column=2, sticky="e")
        self.task_tree = self._tree(page, ("number", "title", "status", "owner"),
                                    [("#", 60), ("Tarefa", 430), ("Status", 160), ("Responsável", 150)], 1)
        self.task_detail_title = tk.StringVar(value="Selecione uma tarefa para ler as instruções completas.")
        ttk.Label(page, textvariable=self.task_detail_title, wraplength=850, foreground=GOLD,
                  font=("Segoe UI", 13, "bold")).grid(row=2, column=0, sticky="w", pady=(18, 12))
        details, self.task_detail = _scroll_text(page, height=7)
        details.grid(row=3, column=0, sticky="nsew")
        self.task_detail.configure(state="disabled")
        self.task_tree.bind("<<TreeviewSelect>>", lambda _event: self._task_selected())
        self.task_query.trace_add("write", lambda *_: self._render_tasks())
        self.task_status.trace_add("write", lambda *_: self._render_tasks())

    def _tree(self, parent, columns, headings, row):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=6)
        for column, (heading, width) in zip(columns, headings):
            tree.heading(column, text=heading)
            tree.column(column, width=width, minwidth=60, stretch=column in ("title", "preview"))
        vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        return tree

    def _build_messages(self):
        page = self.messages_page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        page.rowconfigure(3, weight=1)
        toolbar = ttk.Frame(page)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="Buscar mensagem").grid(row=0, column=0, padx=(0, 12))
        self.message_query = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.message_query).grid(row=0, column=1, sticky="ew", padx=(0, 16))
        ttk.Button(toolbar, text="Escrever mensagem", command=self.toggle_composer).grid(row=0, column=2)
        self.message_tree = self._tree(page, ("sender", "recipient", "date", "preview"),
                                       [("De", 115), ("Para", 115), ("Enviada em", 180), ("Mensagem", 430)], 1)
        self.message_detail_title = tk.StringVar(value="Selecione uma mensagem para ler o conteúdo completo.")
        ttk.Label(page, textvariable=self.message_detail_title, foreground=GOLD,
                  font=("Segoe UI", 13, "bold")).grid(row=2, column=0, sticky="w", pady=(16, 10))
        detail, self.message_detail = _scroll_text(page, height=6)
        detail.grid(row=3, column=0, sticky="nsew")
        self.message_detail.configure(state="disabled")
        self.composer = ttk.LabelFrame(page, text="Nova mensagem", padding=16)
        self.composer.grid(row=4, column=0, sticky="ew", pady=(18, 0))
        self.composer.columnconfigure(0, weight=1)
        controls = ttk.Frame(self.composer)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(controls, text="Para").pack(side="left", padx=(0, 10))
        self.message_to = tk.StringVar(value="Equipe")
        ttk.Combobox(controls, textvariable=self.message_to, values=["Equipe", "Codex", "Antigravity"],
                     state="readonly", width=16).pack(side="left", padx=(0, 20))
        ttk.Label(controls, text="Tarefa (opcional)").pack(side="left", padx=(0, 10))
        self.message_task = tk.StringVar()
        ttk.Entry(controls, textvariable=self.message_task, width=8).pack(side="left")
        text_frame, self.message_body = _scroll_text(self.composer, height=4)
        text_frame.grid(row=1, column=0, sticky="ew")
        bottom = ttk.Frame(self.composer)
        bottom.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.send_button = ttk.Button(bottom, text="Registrar mensagem", command=self.send_message)
        self.send_button.pack(side="left", padx=(0, 12))
        ttk.Button(bottom, text="Fechar", command=self.toggle_composer).pack(side="left")
        self.composer.grid_remove()
        self.message_tree.bind("<<TreeviewSelect>>", lambda _event: self._message_selected())
        self.message_query.trace_add("write", lambda *_: self._render_messages())

    def _render_rows(self, tree, rows):
        wanted = {key for key, _ in rows}
        for existing in tree.get_children():
            if existing not in wanted:
                tree.delete(existing)
        for position, (key, values) in enumerate(rows):
            if tree.exists(key):
                if tuple(tree.item(key, "values")) != tuple(str(value) for value in values):
                    tree.item(key, values=values)
                if tree.index(key) != position:
                    tree.move(key, "", position)
            else:
                tree.insert("", position, iid=key, values=values)

    def _render_tasks(self):
        query, status = self.task_query.get().strip().casefold(), self.task_status.get()
        rows = []
        for task in self.snapshot["tasks"]:
            if status != "Todos os status" and STATUSES.get(task["status"], task["status"]) != status:
                continue
            if query and query not in (str(task["id"]) + " " + task["title"] + " " + task["description"]).casefold():
                continue
            rows.append(("task-" + str(task["id"]), (task["id"], task["title"],
                         STATUSES.get(task["status"], task["status"]), LABELS.get(task["assignee"], task["assignee"]))))
        self._render_rows(self.task_tree, rows)
        self._task_selected()

    def _task_selected(self):
        selected = self.task_tree.selection()
        if not selected:
            self.task_detail_title.set("Selecione uma tarefa para ler as instruções completas.")
            _put_text(self.task_detail, "")
            return
        task = next((item for item in self.snapshot["tasks"] if "task-" + str(item["id"]) == selected[0]), None)
        if task:
            self.task_detail_title.set("#" + str(task["id"]) + " · " + task["title"])
            _put_text(self.task_detail, task["description"] or "Sem instruções adicionais.")

    def _render_messages(self):
        query = self.message_query.get().strip().casefold()
        rows = []
        for message in self.snapshot["messages"]:
            if query and query not in (message["body"] + " " + message["sender"] + " " + message["recipient"]).casefold():
                continue
            preview = " ".join(message["body"].split())[:110]
            rows.append(("message-" + str(message["id"]), (LABELS.get(message["sender"], message["sender"]),
                         LABELS.get(message["recipient"], message["recipient"]), readable_date(message["created_at"]), preview)))
        self._render_rows(self.message_tree, rows)
        self._message_selected()

    def _message_selected(self):
        selected = self.message_tree.selection()
        if not selected:
            self.message_detail_title.set("Selecione uma mensagem para ler o conteúdo completo.")
            _put_text(self.message_detail, "")
            return
        message = next((item for item in self.snapshot["messages"] if "message-" + str(item["id"]) == selected[0]), None)
        if message:
            title = LABELS.get(message["sender"], message["sender"]) + " → " + LABELS.get(message["recipient"], message["recipient"])
            if message.get("task_id"):
                title += " · tarefa #" + str(message["task_id"])
            self.message_detail_title.set(title)
            _put_text(self.message_detail, message["body"])

    def _render_agents(self):
        now = datetime.now(timezone.utc)
        for key, fields in self.agent_fields.items():
            data = self.snapshot["agents"].get(key, {})
            recent = False
            try:
                recent = (now - datetime.fromisoformat(data["last_seen"])).total_seconds() < 40
            except (ValueError, KeyError, TypeError):
                pass
            fields["state"].set("Processo MCP com atividade recente" if recent else "Sem heartbeat recente")
            fields["last_tool"].set("Última chamada MCP:\n" + readable_date(data.get("last_tool_at")))
            fields["last_action"].set("Última atividade:\n" + (data.get("last_action") or "Nenhuma atividade registrada"))

    def refresh(self):
        if self._destroyed:
            return
        if self.workspace is None:
            self.notice.set("Escolha a pasta do projeto compartilhado para acompanhar a equipe. O jogo funciona de forma independente.")
            self.send_button.configure(state="disabled")
            return
        try:
            self.snapshot = read_snapshot(self.workspace)
            self._render_agents()
            self._render_tasks()
            self._render_messages()
            self.notice.set("Projeto conectado: " + self.workspace.name + ". As consultas do painel são somente leitura.")
            try:
                _sender_command(self.workspace)
                self.send_button.configure(state="disabled" if self._sending else "normal")
            except (OSError, ValueError, KeyError, TypeError):
                self.send_button.configure(state="disabled")
                self.notice.set("Leitura conectada. O envio precisa de uma configuração válida da ponte neste projeto.")
        except (OSError, sqlite3.Error, ValueError):
            self.notice.set("Não foi possível consultar a ponte deste projeto. Verifique a pasta escolhida e tente atualizar.")
            self.send_button.configure(state="disabled")

    on_show = refresh

    def choose_workspace(self):
        folder = filedialog.askdirectory(parent=self, title="Escolha o projeto compartilhado entre os agentes")
        if not folder:
            return
        workspace = Path(folder).resolve()
        if not (workspace / ".agent-bridge" / "bridge.sqlite3").is_file():
            self.notice.set("A pasta escolhida ainda não contém uma ponte ARCANUM configurada. Escolha a pasta do projeto.")
            return
        self.workspace = workspace
        try:
            directory = Path(self.store.data_dir)
            directory.mkdir(parents=True, exist_ok=True)
            settings = _settings(directory)
            settings["bridge_workspace"] = str(workspace)
            descriptor, temporary = tempfile.mkstemp(prefix=".desktop-settings-", suffix=".json", dir=str(directory))
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(settings, stream, ensure_ascii=False, indent=2)
                os.replace(temporary, directory / "desktop_settings.json")
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        except OSError:
            self.notice.set("Projeto conectado nesta sessão; não foi possível salvar a preferência.")
        self.refresh()

    def toggle_composer(self):
        if self.composer.winfo_manager():
            self.composer.grid_remove()
        else:
            self.composer.grid()
            self.message_body.focus_set()

    def send_message(self):
        if self._sending or self.workspace is None:
            return
        text = self.message_body.get("1.0", "end-1c").strip()
        if not text or len(text) > 8000:
            self.notice.set("Escreva uma mensagem de até 8.000 caracteres.")
            return
        try:
            command = _sender_command(self.workspace)
            raw_task = self.message_task.get().strip()
            task_id = int(raw_task) if raw_task else None
            if task_id is not None and task_id < 1:
                raise ValueError()
        except (ValueError, OSError, KeyError, TypeError):
            self.notice.set("Confira o número da tarefa e a configuração da ponte do projeto.")
            return
        recipient = {"Equipe": "all", "Codex": "codex", "Antigravity": "antigravity"}[self.message_to.get()]
        command += ["send", "--project", str(self.workspace), "--from-agent", "human", "--to", recipient]
        if task_id is not None:
            command += ["--task-id", str(task_id)]
        # End option parsing so a message beginning with '-' stays a message.
        command += ["--", text]
        workspace = self.workspace
        self._sent_text = text
        self._sending = True
        self.send_button.configure(state="disabled")
        self.notice.set("Registrando sua mensagem na ponte…")

        def worker():
            try:
                result = subprocess.run(command, cwd=str(workspace), shell=False,
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace", timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), env={**os.environ, "PYTHONUTF8": "1"})
                if result.returncode:
                    self._results.put((False, "A ponte não registrou a mensagem. Verifique a tarefa escolhida e tente novamente."))
                else:
                    response = json.loads(result.stdout)
                    if not isinstance(response, dict):
                        raise ValueError("Unexpected bridge response")
                    valid = response.get("sender") == "human" and response.get("recipient") == recipient and response.get("id")
                    message = ("Mensagem registrada. O agente poderá lê-la na próxima consulta à caixa." if valid else
                               "Não foi possível confirmar o envio. Atualize o histórico antes de tentar novamente.")
                    self._results.put((bool(valid), message))
            except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
                self._results.put((False, "Não foi possível confirmar o envio. Atualize o histórico antes de tentar novamente."))
        threading.Thread(target=worker, daemon=True, name="arcanum-human-message").start()
        self.after(120, self._poll_send)

    def _poll_send(self):
        if self._destroyed:
            return
        try:
            success, message = self._results.get_nowait()
        except queue.Empty:
            self.after(120, self._poll_send)
            return
        self._sending = False
        if success and self.message_body.get("1.0", "end-1c").strip() == self._sent_text:
            self.message_body.delete("1.0", "end")
        self.refresh()
        self.notice.set(message)

    def _periodic(self):
        if self._destroyed:
            return
        if self.winfo_ismapped() and not self._sending:
            self.refresh()
        self._timer = self.after(8000, self._periodic)

    def _on_destroy(self, event):
        if event.widget is self:
            self._destroyed = True
            if self._timer:
                try:
                    self.after_cancel(self._timer)
                except tk.TclError:
                    pass


def build_bridge(parent):
    view = BridgeView(parent)
    view.pack(fill="both", expand=True)
    return view


build_coordination = build_bridge
