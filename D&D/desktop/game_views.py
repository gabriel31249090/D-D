"""Native views for the authoritative Python game engine."""
import tkinter as tk
from tkinter import messagebox, ttk

from backend.services import DomainError
from .style import COLORS, button, heading, scroll_list
from .tools_view import detail_text, display

ABILITIES = (("strength", "Força", 15), ("dexterity", "Destreza", 14),
             ("constitution", "Constituição", 13), ("intelligence", "Inteligência", 10),
             ("wisdom", "Sabedoria", 12), ("charisma", "Carisma", 8))


def input_field(parent, label, widget, width=None):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=label).pack(anchor="w", pady=(0, 4))
    field = widget(frame)
    if width:
        field.configure(width=width)
    field.pack(fill="x")
    return frame


def attempt(parent, action):
    try:
        return action()
    except (ValueError, RuntimeError) as error:
        messagebox.showerror("ARCANUM", str(error), parent=parent)
    except DomainError as error:
        messagebox.showerror("ARCANUM", error.message, parent=parent)
    return None


def build_characters(parent):
    heading(parent, "Personagens", "Crie um guerreiro de nível 1 e consulte a ficha calculada pelas regras de 2014.")
    split = ttk.Panedwindow(parent, orient="horizontal")
    split.pack(fill="both", expand=True)
    left, right = ttk.Frame(split), ttk.Frame(split, padding=(18, 0, 0, 0))
    split.add(left, weight=2)
    split.add(right, weight=3)
    characters = []
    ttk.Label(left, text="Fichas salvas", style="Section.TLabel").pack(anchor="w")
    box, listing = scroll_list(left, height=5)
    box.pack(fill="x", pady=9)
    detail, info = detail_text(left)
    detail.pack(fill="both", expand=True)
    name = tk.StringVar()
    ttk.Label(right, text="Nova ficha", style="Section.TLabel").pack(anchor="w", pady=(0, 12))
    input_field(right, "Nome", lambda p: ttk.Entry(p, textvariable=name)).pack(fill="x", pady=(0, 12))
    attributes = ttk.Frame(right)
    attributes.pack(fill="x")
    scores = {}
    for index, (key, label, value) in enumerate(ABILITIES):
        variable = tk.StringVar(value=str(value))
        scores[key] = variable
        attributes.columnconfigure(index % 2, weight=1)
        field = input_field(attributes, label, lambda p, var=variable: ttk.Spinbox(p, textvariable=var, from_=3, to=20))
        field.grid(row=index // 2, column=index % 2, sticky="ew", padx=(0, 10), pady=(0, 9))
    armor = {"Cota de malha": "chain_mail", "Armadura de couro": "leather", "Sem armadura": "none"}
    styles = {"Defesa": "defense", "Duelismo": "dueling"}
    equipped, style, shield = tk.StringVar(value=next(iter(armor))), tk.StringVar(value="Defesa"), tk.BooleanVar(value=True)
    equipment = ttk.Frame(right)
    equipment.pack(fill="x")
    for label, variable, options in (("Armadura", equipped, armor), ("Estilo", style, styles)):
        field = input_field(equipment, label, lambda p, v=variable, o=options:
                            ttk.Combobox(p, textvariable=v, state="readonly", values=tuple(o), width=13))
        field.pack(side="left", fill="x", expand=True, padx=(0, 10))
    ttk.Checkbutton(right, text="Usar escudo", variable=shield).pack(anchor="w", pady=9)

    def selected(_=None):
        indices = listing.curselection()
        if not indices:
            display(info, "As fichas salvas aparecem aqui.")
            rest.configure(state="disabled")
            return
        hero = characters[indices[0]]
        lines = [hero["name"], f"PV {hero['current_hp']}/{hero['max_hp']}    CA {hero['armor_class']}", "",
                 *[f"{label}  {hero['abilities'][key]}  ({hero['ability_modifiers'][key]:+d})"
                   for key, label, _ in ABILITIES],
                 "", f"Iniciativa  {hero['initiative_bonus']:+d}"]
        for attack in hero["attacks"]:
            lines.append(f"{attack['name']}  {attack['attack_bonus']:+d}  ·  {attack['damage_expression']}")
        display(info, "\n".join(lines))
        rest.configure(state="disabled" if hero["active_combat_id"] else "normal")

    def refresh(pick=None):
        characters[:] = parent.store.characters()
        listing.delete(0, "end")
        for index, hero in enumerate(characters):
            listing.insert("end", hero["name"])
            if hero["id"] == pick or (pick is None and index == 0):
                listing.selection_set(index)
        selected()

    def create():
        def write():
            return parent.store.character({"name": name.get(), "abilities": {k: int(v.get()) for k, v in scores.items()},
                "equipment": {"armor": armor[equipped.get()], "shield": shield.get()}, "fighting_style": styles[style.get()]})
        if hero := attempt(parent, write):
            name.set("")
            refresh(hero["id"])

    def rest_character():
        chosen = listing.curselection()
        if chosen:
            identifier = characters[chosen[0]]["id"]
            if attempt(parent, lambda: parent.store.rest(identifier)):
                refresh(identifier)

    button(right, "Salvar personagem", create, True).pack(anchor="w", pady=(10, 0))
    rest = button(left, "Recuperar PV de treino", rest_character)
    rest.pack(anchor="w", pady=(10, 0))
    listing.bind("<<ListboxSelect>>", selected)
    refresh()


def build_groups(parent):
    heading(parent, "Grupos", "Reúna os personagens que participarão dos encontros.")
    split = ttk.Panedwindow(parent, orient="horizontal")
    split.pack(fill="both", expand=True)
    left, right = ttk.Frame(split), ttk.Frame(split, padding=(20, 0, 0, 0))
    split.add(left, weight=2)
    split.add(right, weight=3)
    ttk.Label(left, text="Grupos salvos", style="Section.TLabel").pack(anchor="w")
    box, groups = scroll_list(left, height=6)
    box.pack(fill="x", pady=12)
    detail, info = detail_text(left)
    detail.pack(fill="both", expand=True)
    heroes = parent.store.characters()
    names = {hero["id"]: hero["name"] for hero in heroes}
    name = tk.StringVar()
    ttk.Label(right, text="Novo grupo", style="Section.TLabel").pack(anchor="w", pady=(0, 12))
    input_field(right, "Nome do grupo", lambda p: ttk.Entry(p, textvariable=name)).pack(fill="x", pady=(0, 14))
    ttk.Label(right, text="Selecione os integrantes com Ctrl ou Shift").pack(anchor="w")
    selection, members = scroll_list(right, height=7, multiple=True)
    selection.pack(fill="both", expand=True, pady=10)
    for hero in heroes:
        members.insert("end", hero["name"])
    parties = []

    def show(_=None):
        index = groups.curselection()
        if index:
            party = parties[index[0]]
            display(info, party["name"] + "\n\n" + "\n".join(names.get(key, key) for key in party["character_ids"]))
        else:
            display(info, "Os grupos salvos aparecem aqui.")

    def refresh():
        parties[:] = parent.store.parties()
        groups.delete(0, "end")
        for party in parties:
            groups.insert("end", party["name"])
        if parties:
            groups.selection_set("end")
        show()

    def save():
        data = {"name": name.get(), "character_ids": [heroes[i]["id"] for i in members.curselection()]}
        if attempt(parent, lambda: parent.store.party(data)):
            name.set("")
            members.selection_clear(0, "end")
            refresh()

    button(right, "Salvar grupo", save, True).pack(anchor="w")
    if not heroes:
        button(right, "Criar personagem", lambda: parent.app.show("Personagens")).pack(anchor="w", pady=10)
    groups.bind("<<ListboxSelect>>", show)
    refresh()


def build_dice(parent):
    heading(parent, "Dados", "Role dados individuais ou uma expressão como 2d6+3.")
    expression = tk.StringVar(value="1d20")
    mode = tk.StringVar(value="Normal")
    options = {"Normal": "normal", "Vantagem": "advantage", "Desvantagem": "disadvantage"}
    row = ttk.Frame(parent)
    row.pack(fill="x")
    input_field(row, "Expressão", lambda p: ttk.Entry(p, textvariable=expression)).pack(side="left")
    input_field(row, "Modo", lambda p: ttk.Combobox(p, textvariable=mode, values=tuple(options),
                                                   state="readonly")).pack(side="left", padx=15)
    result = tk.StringVar(value="Aguardando rolagem")
    ttk.Label(parent, textvariable=result, style="Title.TLabel").pack(anchor="w", pady=22)
    box, history = scroll_list(parent)
    box.pack(fill="both", expand=True)

    def roll():
        data = attempt(parent, lambda: parent.store.roll(expression.get().strip(), options[mode.get()]))
        if data:
            result.set(f"Total  {data['total']}")
            history.insert(0, f"{data['expression']}  ·  Dados {data['rolls']}  ·  Total {data['total']}")

    button(row, "Rolar dados", roll, True).pack(side="left", anchor="s")


def build_arena(parent):
    heading(parent, "Arena", "Monte um encontro de treino, controle os dois lados e reveja as rodadas salvas.")
    notebook = ttk.Notebook(parent)
    notebook.pack(fill="both", expand=True)
    prep, field = ttk.Frame(notebook, padding=14), ttk.Frame(notebook, padding=14)
    notebook.add(prep, text="Encontros")
    notebook.add(field, text="Batalha")
    parties = parent.store.parties()
    selection, count = tk.StringVar(), tk.StringVar(value="1")
    row = ttk.Frame(prep)
    row.pack(fill="x")
    party_box = ttk.Combobox(row, textvariable=selection, state="readonly",
                             values=[p["name"] for p in parties], width=20)
    party_box.pack(side="left")
    if parties:
        party_box.current(0)
    ttk.Label(row, text="Goblins de treino").pack(side="left", padx=(15, 8))
    ttk.Spinbox(row, textvariable=count, from_=1, to=12, width=5).pack(side="left")
    ttk.Label(prep, text="Encontros salvos", style="Section.TLabel").pack(anchor="w", pady=(24, 10))
    box, encounters = scroll_list(prep)
    box.pack(fill="both", expand=True)
    records = []
    current = None
    active = tk.StringVar(value="Abra ou inicie um encontro.")
    status = ttk.Label(field, textvariable=active, style="Section.TLabel")
    status.pack(anchor="w", pady=(0, 7))
    canvas = tk.Canvas(field, height=230, bg="#151E2C", highlightthickness=1, highlightbackground=COLORS["line"])
    canvas.pack(fill="both", expand=True)
    actions = ttk.Frame(field)
    actions.pack(fill="x", pady=10)
    target = ttk.Combobox(actions, width=21, state="readonly")
    target.pack(side="left", fill="x", expand=True)
    report_frame, report = detail_text(field, height=5)
    report_frame.pack(fill="x")
    targets = []
    coords = {}
    feedback = ""

    def draw(_=None):
        canvas.delete("all")
        coords.clear()
        if not current:
            return
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width <= 10 or height <= 10: return
        canvas.create_polygon(width * .06, height * .86, width * .22, height * .24,
                              width * .78, height * .24, width * .94, height * .86,
                              fill="#222F40", outline="#54647F")
        for team, center, colour in (("party", .28, "#8EBBD6"), ("enemy", .72, "#E5A394")):
            side = [actor for actor in current["combatants"] if actor["team"] == team]
            for i, actor in enumerate(side):
                column, row_index = i % 3, i // 3
                x = width * center + (column - (min(3, len(side))-1)/2) * width * .10
                y = height * .29 + (row_index + .5) * min(56, height * .58 / ((len(side)+2)//3))
                tag = "actor_" + actor["id"]
                coords[actor["id"]] = (x, y, tag)
                outline = COLORS["gold"] if actor["id"] == current["current_actor_id"] else "#34415C"
                fill = colour if actor["current_hp"] else "#596173"
                canvas.create_oval(x-14,y-14,x+14,y+14,fill=fill,outline=outline,width=2,tags=(tag,))
                canvas.create_text(x,y,text=actor["name"][0:1].upper(),fill="#17202A",
                                   font=("Segoe UI Semibold", 11),tags=(tag,))
                canvas.create_text(x,y+21,text=f"{actor['current_hp']}/{actor['max_hp']}",fill=COLORS["text"],
                                   font=("Segoe UI", 9),tags=(tag,))
        canvas.create_text(width / 2, 16, text=feedback, fill=COLORS["gold"], font=("Segoe UI", 11))

    def render():
        if not current:
            return
        actors = {actor["id"]: actor for actor in current["combatants"]}
        actor = actors.get(current["current_actor_id"])
        active.set(f"Rodada {current['round']}  ·  {actor['name']}" if actor else
                   ("Encontro encerrado  ·  Vitória do grupo" if current["winner"] == "party"
                    else "Encontro encerrado  ·  Vitória dos inimigos"))
        targets[:] = [candidate for candidate in actors.values() if actor and candidate["team"] != actor["team"]
                      and candidate["current_hp"] > 0]
        target.configure(values=[f"{item['name']}  ·  {item['current_hp']} PV" for item in targets])
        if targets: target.current(0)
        else: target.set("")
        attack_button.configure(state="normal" if actor and actor["action_available"] and targets else "disabled")
        turn_button.configure(state="normal" if actor else "disabled")
        lines = []
        for event in parent.store.events(current["id"]):
            payload = event["payload"]
            kind = event["type"]
            if kind == "attack_resolved":
                a = actors.get(payload["actor_id"], {})
                b = actors.get(payload["target_id"], {})
                result = f"{payload['damage']} de dano" if payload["hit"] else "errou"
                lines.append(f"{a.get('name', 'Combatente')} → {b.get('name', 'Alvo')}  ·  {result}")
            elif kind == "turn_started":
                lines.append(f"Rodada {payload['round']}  ·  {actors.get(payload['actor_id'], {}).get('name', 'Turno iniciado')}")
            elif kind == "combat_started":
                lines.append("Encontro iniciado")
            elif kind == "combat_completed":
                lines.append("Encontro encerrado")
        display(report, "\n".join(lines))
        report.see("end")
        draw()

    def act(kind):
        nonlocal current, feedback
        if not current or not current["current_actor_id"]:
            return
        actor = next(a for a in current["combatants"] if a["id"] == current["current_actor_id"])
        command = {"type": kind, "actor_id": actor["id"], "expected_version": current["version"]}
        if kind == "attack":
            if target.current() < 0:
                return
            command.update(target_id=targets[target.current()]["id"], attack_id=actor["attacks"][0]["id"])
        result = attempt(parent, lambda: parent.store.action(current["id"], command))
        if not result:
            current = next((c for c in parent.store.combats() if c["id"] == current["id"]), current)
            render()
            return
        current = result["combat"]
        hit = next((e["payload"] for e in result["events"] if e["type"] == "attack_resolved"), None)
        feedback = (f"{hit['damage']} de dano" if hit["hit"] else "Ataque errou") if hit else ""
        render()
        if hit and hit["actor_id"] in coords and hit["target_id"] in coords:
            x, _, tag = coords[hit["actor_id"]]
            dx = 20 if coords[hit["target_id"]][0] > x else -20
            canvas.move(tag, dx, 0)
            canvas.after(140, draw)

    def refresh():
        records[:] = list(reversed(parent.store.combats()))
        encounters.delete(0, "end")
        names = {p["id"]: p["name"] for p in parties}
        for entry in records:
            label = "Encerrado" if entry["status"] == "completed" else "Em andamento"
            encounters.insert("end", f"{names.get(entry['party_id'], 'Grupo')}  ·  {label}  ·  Rodada {entry['round']}")

    def open_encounter(_=None):
        nonlocal current, feedback
        chosen = encounters.curselection()
        if chosen:
            current, feedback = records[chosen[0]], ""
            notebook.select(field)
            render()

    def start():
        nonlocal current, feedback
        if party_box.current() < 0:
            messagebox.showinfo("Escolher grupo", "Crie um grupo para iniciar um encontro.", parent=parent)
            return
        encounter = attempt(parent, lambda: parent.store.encounter(parties[party_box.current()]["id"], int(count.get())))
        if encounter:
            current, feedback = encounter, ""
            notebook.select(field)
            render()
            refresh()

    button(row, "Iniciar encontro", start, True).pack(side="left", padx=10)
    button(prep, "Abrir selecionado", open_encounter).pack(anchor="w", pady=(10, 0))
    attack_button = button(actions, "Atacar alvo", lambda: act("attack"), True)
    attack_button.pack(side="left", padx=8)
    turn_button = button(actions, "Encerrar turno", lambda: act("end_turn"))
    turn_button.pack(side="left")
    for control in (attack_button, turn_button): control.configure(state="disabled")
    canvas.bind("<Configure>", draw)
    encounters.bind("<Double-Button-1>", open_encounter)
    notebook.bind("<<NotebookTabChanged>>", lambda _: refresh() if notebook.select() == str(prep) else None)
    refresh()
