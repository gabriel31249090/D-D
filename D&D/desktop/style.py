from tkinter import ttk
import tkinter as tk

COLORS = {
    "bg": "#101521", "surface": "#192131", "raised": "#222D40",
    "text": "#F1EDDF", "muted": "#B3BFD1", "gold": "#E9BE75",
    "line": "#374359", "green": "#93D4AF", "red": "#F0A5A5",
}


def configure_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    root.option_add("*Font", ("Segoe UI", 12))
    root.option_add("*Listbox.background", COLORS["surface"])
    root.option_add("*Listbox.foreground", COLORS["text"])
    root.option_add("*Listbox.selectBackground", "#455777")
    root.option_add("*Listbox.selectForeground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.background", COLORS["surface"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    style.configure(".", font=("Segoe UI", 12), background=COLORS["bg"], foreground=COLORS["text"],
                    fieldbackground=COLORS["surface"], bordercolor=COLORS["line"],
                    lightcolor=COLORS["line"], darkcolor=COLORS["line"])
    style.configure("Card.TFrame", background=COLORS["surface"])
    style.configure("Card.TLabel", background=COLORS["surface"])
    style.configure("Title.TLabel", font=("Cambria", 31, "bold"))
    style.configure("Section.TLabel", font=("Segoe UI Semibold", 15))
    style.configure("Muted.TLabel", foreground=COLORS["muted"])
    style.configure("TButton", padding=(14, 10), background=COLORS["raised"])
    style.map("TButton", background=[("active", "#35435D")], foreground=[("disabled", "#8994A7")])
    style.configure("Primary.TButton", background=COLORS["gold"], foreground="#201A11")
    style.map("Primary.TButton", background=[("disabled", "#3C4351"), ("active", "#F7D9A1")],
              foreground=[("disabled", "#B3BFD1"), ("!disabled", "#201A11")])
    style.configure("Nav.TButton", anchor="w", padding=(16, 9), background=COLORS["surface"],
                    borderwidth=0)
    style.configure("Selected.Nav.TButton", background="#344054", foreground=COLORS["gold"])
    for name in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(name, padding=7, insertcolor=COLORS["text"], arrowcolor=COLORS["text"])
    style.map("TCombobox", fieldbackground=[("readonly", COLORS["surface"])],
              foreground=[("readonly", COLORS["text"])])
    style.configure("TNotebook", borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), background=COLORS["surface"])
    style.map("TNotebook.Tab", foreground=[("selected", COLORS["gold"])],
              background=[("selected", COLORS["raised"])])
    style.configure("Treeview", rowheight=40, background=COLORS["surface"], fieldbackground=COLORS["surface"])
    style.configure("Treeview.Heading", padding=8, font=("Segoe UI Semibold", 11))
    style.map("Treeview", background=[("selected", "#405475")])


def heading(parent, title, subtitle=""):
    ttk.Label(parent, text=title, style="Title.TLabel").pack(anchor="w")
    if subtitle:
        label = ttk.Label(parent, text=subtitle, style="Muted.TLabel", justify="left")
        label.pack(anchor="w", fill="x", pady=(4, 20))
        label.bind("<Configure>", lambda e: label.configure(wraplength=e.width))


def card(parent, padding=20):
    return ttk.Frame(parent, padding=padding, style="Card.TFrame")


def button(parent, text, command, primary=False):
    return ttk.Button(parent, text=text, command=command, style="Primary.TButton" if primary else "TButton")


def text_area(parent, height=6):
    return tk.Text(parent, height=height, width=20, wrap="word", background=COLORS["surface"],
                   foreground=COLORS["text"], insertbackground=COLORS["gold"], relief="flat",
                   padx=12, pady=9, highlightthickness=1, highlightbackground=COLORS["line"],
                   highlightcolor=COLORS["gold"], selectbackground="#405475")


def scroll_list(parent, height=8, multiple=False):
    frame = ttk.Frame(parent)
    scrollbar = ttk.Scrollbar(frame)
    listing = tk.Listbox(frame, height=height, width=20, activestyle="none", relief="flat",
                         highlightthickness=1, highlightcolor=COLORS["gold"],
                         highlightbackground=COLORS["line"], yscrollcommand=scrollbar.set,
                         selectmode="extended" if multiple else "browse", exportselection=False)
    scrollbar.configure(command=listing.yview)
    listing.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return frame, listing
