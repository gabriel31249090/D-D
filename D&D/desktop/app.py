"""Launch the local Windows desktop application."""
import argparse
import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from .game import GameStore
from .game_views import build_arena, build_characters, build_groups, build_dice
from .style import COLORS, button, card, configure_theme, heading
from .tools_view import build_campaigns, build_library


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("ARCANUM  ·  Ferramentas de mesa")
        self.geometry("1180x790")
        self.minsize(850, 610)
        self.configure(background=COLORS["bg"])
        configure_theme(self)
        self.store = GameStore()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.page = None
        self.page_name = None
        self.callbacks_failed = []
        self.nav = {}

        rail = tk.Frame(self, background=COLORS["surface"], width=214)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        tk.Label(rail, text="ARCANUM", background=COLORS["surface"], foreground=COLORS["gold"],
                 font=("Cambria", 22, "bold"), anchor="w").pack(fill="x", padx=18, pady=(25, 4))
        tk.Label(rail, text="Mesa de RPG", background=COLORS["surface"], foreground=COLORS["muted"],
                 anchor="w").pack(fill="x", padx=20, pady=(0, 16))
        self.pages = {
            "Visão geral": self.home,
            "Personagens": build_characters, "Grupos": build_groups,
            "Arena": build_arena, "Dados": build_dice, "Campanhas": build_campaigns,
            "Mapas": self.maps, "Biblioteca": build_library, "Coordenação": self.bridge,
        }
        for page in self.pages:
            item = ttk.Button(rail, text=page, style="Nav.TButton",
                              command=lambda name=page: self.show(name))
            item.pack(fill="x", padx=9, pady=1)
            self.nav[page] = item
        tk.Label(rail, text="Edição para Windows", background=COLORS["surface"], foreground=COLORS["muted"],
                 font=("Segoe UI", 10), anchor="w").pack(side="bottom", fill="x", padx=20, pady=14)
        self.host = ttk.Frame(self, padding=(28, 24, 28, 22))
        self.host.pack(fill="both", expand=True)
        self.show("Visão geral")

    def show(self, name):
        if name == self.page_name:
            return
        if self.page:
            if not getattr(self.page, "leave_page", lambda: True)():
                return
            self.page.destroy()
            self.nav[self.page_name].configure(style="Nav.TButton")
        self.page_name = name
        self.nav[name].configure(style="Selected.Nav.TButton")
        self.page = ttk.Frame(self.host)
        self.page.pack(fill="both", expand=True)
        self.page.store = self.store
        self.page.app = self
        self.pages[name](self.page)

    def home(self, parent):
        heading(parent, "Sua mesa de RPG", "Prepare a sessão, reúna o grupo e acompanhe os encontros em um só lugar.")
        counts = (("Personagens", len(self.store.characters())), ("Grupos", len(self.store.parties())),
                  ("Arena", len(self.store.combats())))
        row = ttk.Frame(parent)
        row.pack(fill="x")
        for column, (name, count) in enumerate(counts):
            row.columnconfigure(column, weight=1, uniform="summary")
            tile = card(row)
            tile.grid(row=0, column=column, padx=(0 if column == 0 else 10, 0), sticky="nsew")
            ttk.Label(tile, text=name, style="Card.TLabel").pack(anchor="w")
            ttk.Label(tile, text=str(count), style="Card.TLabel", font=("Cambria", 29),
                      foreground=COLORS["gold"]).pack(anchor="w", pady=8)
            button(tile, "Abrir", lambda page=name: self.show(page)).pack(anchor="w")
        ttk.Label(parent, text="Preparar sessão", style="Section.TLabel").pack(anchor="w", pady=(26, 12))
        for name, description in (("Campanhas", "Anotações, lugares, personagens e missões"),
                                  ("Mapas", "Grade de encontro e geração de masmorras"),
                                  ("Biblioteca", "Livros, fichas de Valebruma e materiais locais"),
                                  ("Coordenação", "Tarefas e mensagens do Codex e do Antigravity")):
            row = card(parent, padding=(14, 7))
            row.pack(fill="x", pady=(0, 7))
            button(row, name, lambda page=name: self.show(page)).pack(side="left")
            ttk.Label(row, text=description, style="Card.TLabel", foreground=COLORS["muted"]).pack(
                side="left", padx=14)

    def bridge(self, parent):
        from .bridge_view import build_bridge
        build_bridge(parent)

    def maps(self, parent):
        from .map_view import build_map
        view = build_map(parent)
        if hasattr(view, "has_unsaved_changes"):
            def leave():
                if not view.has_unsaved_changes():
                    return True
                selected = messagebox.askyesnocancel("Mapa alterado", "Salvar o mapa antes de sair?", parent=self)
                return selected is False or (selected is True and bool(view.save_current()))
            parent.leave_page = leave

    def close(self):
        if self.page and not getattr(self.page, "leave_page", lambda: True)():
            return
        self.store.engine.dispose()
        self.destroy()

    def report_callback_exception(self, exc_type, exc, traceback):
        self.callbacks_failed.append(exc)
        if "--smoke-test" in sys.argv:
            super().report_callback_exception(exc_type, exc, traceback)
        else:
            messagebox.showerror("ARCANUM", str(exc), parent=self)


def main():
    parser = argparse.ArgumentParser(description="ARCANUM para Windows")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except OSError:
            pass
    app = App()
    if args.smoke_test:
        for page in app.pages:
            app.show(page)
            app.update()
        print(f"ARCANUM Desktop: {len(app.pages)} telas; {len(app.callbacks_failed)} erros de interface")
        status = int(bool(app.callbacks_failed))
        app.store.engine.dispose()
        app.destroy()
        return status
    app.deiconify()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
