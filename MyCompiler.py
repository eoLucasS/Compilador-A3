"""
BASIC-to-C Compiler — A visual compiler that translates BASIC source code into C.
Features a modern dark-themed IDE with syntax highlighting, line numbers, and file I/O.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from MyLexer import Lexer, CompilerError, TokenType
from MyParser import Parser
from MyEmitter import Emitter

# ── Color palette ──────────────────────────────────────────────────────────────

COLORS = {
    "bg":          "#1e1e2e",
    "bg_light":    "#282840",
    "bg_panel":    "#232338",
    "fg":          "#cdd6f4",
    "fg_dim":      "#6c7086",
    "accent":      "#89b4fa",
    "accent_hover":"#74c7ec",
    "green":       "#a6e3a1",
    "red":         "#f38ba8",
    "yellow":      "#f9e2af",
    "peach":       "#fab387",
    "mauve":       "#cba6f7",
    "surface":     "#313244",
    "border":      "#45475a",
    "selection":   "#3a3a5c",
}

# Syntax highlight tags
HIGHLIGHT_RULES = {
    "keyword": {"foreground": "#cba6f7", "font": ("Cascadia Code", 11, "bold")},
    "string":  {"foreground": "#a6e3a1"},
    "number":  {"foreground": "#fab387"},
    "comment": {"foreground": "#6c7086", "font": ("Cascadia Code", 11, "italic")},
    "operator":{"foreground": "#89dceb"},
}

BASIC_KEYWORDS = {
    "PRINT", "INPUT", "LET", "IF", "THEN", "ENDIF",
    "WHILE", "REPEAT", "ENDWHILE", "LABEL", "GOTO",
}

FONT_MONO = ("Cascadia Code", 11)
FONT_UI   = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 11, "bold")

EXAMPLES_DIR = Path(__file__).parent / "examples"


class LineNumbers(tk.Canvas):
    """Displays line numbers synchronized with a Text widget."""

    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, width=45, highlightthickness=0, **kwargs)
        self.text_widget = text_widget

    def redraw(self, _event=None):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(
                38, y, anchor="ne", text=linenum,
                fill=COLORS["fg_dim"], font=FONT_MONO,
            )
            i = self.text_widget.index(f"{i}+1line")


class CodeEditor(tk.Frame):
    """Text editor with line numbers and syntax highlighting."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg_panel"])

        self.line_numbers = LineNumbers(
            self, None, bg=COLORS["bg_panel"],
        )

        self.text = tk.Text(
            self,
            wrap="none",
            font=FONT_MONO,
            bg=COLORS["bg_panel"],
            fg=COLORS["fg"],
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["selection"],
            selectforeground=COLORS["fg"],
            relief="flat",
            undo=True,
            maxundo=-1,
            padx=8, pady=8,
            borderwidth=0,
            tabs=("4c",),
        )

        scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self._on_scroll_y)
        scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.line_numbers.pack(side="left", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        self.line_numbers.text_widget = self.text

        # Configure syntax highlight tags
        for tag, config in HIGHLIGHT_RULES.items():
            self.text.tag_configure(tag, **config)

        self.text.bind("<KeyRelease>", self._on_change)
        self.text.bind("<MouseWheel>", self._on_change)
        self.text.bind("<<Modified>>", self._on_change)

    def _on_scroll_y(self, *args):
        self.text.yview(*args)
        self.line_numbers.redraw()

    def _on_change(self, _event=None):
        self.line_numbers.redraw()
        self.highlight_syntax()

    def highlight_syntax(self):
        content = self.text.get("1.0", "end-1c")
        for tag in HIGHLIGHT_RULES:
            self.text.tag_remove(tag, "1.0", "end")

        for i, line in enumerate(content.split("\n"), 1):
            col = 0
            stripped = line.lstrip()

            # Comments
            comment_pos = line.find("#")
            if comment_pos >= 0:
                self.text.tag_add("comment", f"{i}.{comment_pos}", f"{i}.end")

            j = 0
            while j < len(line):
                ch = line[j]

                if ch == '#':
                    break

                # Strings
                if ch == '"':
                    end = line.find('"', j + 1)
                    if end == -1:
                        end = len(line) - 1
                    self.text.tag_add("string", f"{i}.{j}", f"{i}.{end + 1}")
                    j = end + 1
                    continue

                # Numbers
                if ch.isdigit():
                    start = j
                    while j < len(line) and (line[j].isdigit() or line[j] == '.'):
                        j += 1
                    self.text.tag_add("number", f"{i}.{start}", f"{i}.{j}")
                    continue

                # Words (keywords / identifiers)
                if ch.isalpha() or ch == '_':
                    start = j
                    while j < len(line) and (line[j].isalnum() or line[j] == '_'):
                        j += 1
                    word = line[start:j]
                    if word in BASIC_KEYWORDS:
                        self.text.tag_add("keyword", f"{i}.{start}", f"{i}.{j}")
                    continue

                # Operators
                if ch in "+-*/=<>!":
                    start = j
                    j += 1
                    if j < len(line) and line[j] in "=":
                        j += 1
                    self.text.tag_add("operator", f"{i}.{start}", f"{i}.{j}")
                    continue

                j += 1

    def get_content(self):
        return self.text.get("1.0", "end-1c")

    def set_content(self, content):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self._on_change()


class OutputPanel(tk.Frame):
    """Read-only text panel for displaying output."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg_panel"])

        self.text = tk.Text(
            self,
            wrap="word",
            font=FONT_MONO,
            bg=COLORS["bg_panel"],
            fg=COLORS["fg"],
            relief="flat",
            state="disabled",
            padx=8, pady=8,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def set_content(self, content, tag=None):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        if tag:
            self.text.tag_configure(tag, foreground=COLORS.get(tag, COLORS["fg"]))
            self.text.tag_add(tag, "1.0", "end")
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


class StatusBar(tk.Frame):
    """Bottom status bar showing compiler state."""

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["surface"], height=28)
        self.pack_propagate(False)

        self.label = tk.Label(
            self, text="Ready",
            bg=COLORS["surface"], fg=COLORS["fg_dim"],
            font=FONT_UI, anchor="w", padx=12,
        )
        self.label.pack(side="left", fill="x", expand=True)

        self.pos_label = tk.Label(
            self, text="Ln 1, Col 1",
            bg=COLORS["surface"], fg=COLORS["fg_dim"],
            font=FONT_UI, padx=12,
        )
        self.pos_label.pack(side="right")

    def set_message(self, text, color=None):
        self.label.configure(text=text, fg=color or COLORS["fg_dim"])

    def set_position(self, line, col):
        self.pos_label.configure(text=f"Ln {line}, Col {col}")


class CompilerApp:
    def __init__(self, root):
        self.root = root
        self.current_file = None
        self._setup_window()
        self._setup_styles()
        self._build_menu()
        self._build_toolbar()
        self._build_main_area()
        self._build_status_bar()
        self._bind_shortcuts()
        self._load_default_example()

    def _setup_window(self):
        self.root.title("BASIC → C  Compiler")
        self.root.geometry("1400x780")
        self.root.minsize(900, 500)
        self.root.configure(bg=COLORS["bg"])

        # Try to set window icon
        try:
            icon_path = Path(__file__).parent / "assets" / "img" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("TButton", background=COLORS["surface"], foreground=COLORS["fg"],
                        borderwidth=0, padding=(16, 6))
        style.map("TButton",
                  background=[("active", COLORS["accent"]), ("pressed", COLORS["accent_hover"])],
                  foreground=[("active", COLORS["bg"]), ("pressed", COLORS["bg"])])

        style.configure("Accent.TButton", background=COLORS["accent"], foreground=COLORS["bg"],
                        font=("Segoe UI", 11, "bold"), padding=(24, 8))
        style.map("Accent.TButton",
                  background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["green"])])

        style.configure("Vertical.TScrollbar",
                        background=COLORS["surface"], troughcolor=COLORS["bg_panel"],
                        borderwidth=0, arrowsize=0)
        style.configure("Horizontal.TScrollbar",
                        background=COLORS["surface"], troughcolor=COLORS["bg_panel"],
                        borderwidth=0, arrowsize=0)

        style.configure("TPanedwindow", background=COLORS["border"])

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=COLORS["surface"], fg=COLORS["fg"],
                         activebackground=COLORS["accent"], activeforeground=COLORS["bg"],
                         relief="flat", borderwidth=0)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["surface"], fg=COLORS["fg"],
                           activebackground=COLORS["accent"], activeforeground=COLORS["bg"])
        file_menu.add_command(label="New            Ctrl+N", command=self._new_file)
        file_menu.add_command(label="Open...        Ctrl+O", command=self._open_file)
        file_menu.add_command(label="Save           Ctrl+S", command=self._save_file)
        file_menu.add_command(label="Save As...     Ctrl+Shift+S", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export C Code...", command=self._export_c)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Examples menu
        examples_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["surface"], fg=COLORS["fg"],
                               activebackground=COLORS["accent"], activeforeground=COLORS["bg"])
        self._populate_examples_menu(examples_menu)
        menubar.add_cascade(label="Examples", menu=examples_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["surface"], fg=COLORS["fg"],
                           activebackground=COLORS["accent"], activeforeground=COLORS["bg"])
        help_menu.add_command(label="Language Reference", command=self._show_lang_ref)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _populate_examples_menu(self, menu):
        if not EXAMPLES_DIR.exists():
            menu.add_command(label="(no examples found)", state="disabled")
            return
        files = sorted(EXAMPLES_DIR.glob("*.basic"))
        if not files:
            menu.add_command(label="(no examples found)", state="disabled")
            return
        for f in files:
            name = f.stem.replace("_", " ").title()
            menu.add_command(label=name, command=lambda p=f: self._load_example(p))

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg=COLORS["bg"], padx=16, pady=8)
        toolbar.pack(fill="x")

        title = tk.Label(
            toolbar, text="BASIC → C  Compiler",
            bg=COLORS["bg"], fg=COLORS["accent"],
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(side="left")

        # Compile button (right side)
        self.compile_btn = tk.Button(
            toolbar, text="▶  Compile",
            bg=COLORS["accent"], fg=COLORS["bg"],
            activebackground=COLORS["accent_hover"], activeforeground=COLORS["bg"],
            font=("Segoe UI", 11, "bold"),
            relief="flat", cursor="hand2",
            padx=20, pady=6,
            command=self._compile,
        )
        self.compile_btn.pack(side="right", padx=(8, 0))

        shortcut_hint = tk.Label(
            toolbar, text="Ctrl+Enter",
            bg=COLORS["bg"], fg=COLORS["fg_dim"],
            font=("Segoe UI", 9),
        )
        shortcut_hint.pack(side="right")

    def _build_main_area(self):
        # Main container with 3 panels
        main = tk.Frame(self.root, bg=COLORS["bg"], padx=16)
        main.pack(fill="both", expand=True, pady=(0, 4))

        # Use grid for 3 equal columns
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=2)
        main.rowconfigure(1, weight=1)

        # Panel headers
        for col, title in enumerate(["Source Code (BASIC)", "Symbol Table", "Compiled Output (C)"]):
            lbl = tk.Label(
                main, text=title,
                bg=COLORS["bg"], fg=COLORS["fg"],
                font=FONT_TITLE, anchor="w",
            )
            lbl.grid(row=0, column=col, sticky="w", padx=(4, 12), pady=(0, 4))

        # Editor panel
        editor_frame = tk.Frame(main, bg=COLORS["border"], padx=1, pady=1)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.editor = CodeEditor(editor_frame)
        self.editor.pack(fill="both", expand=True)

        # Symbol table panel
        symbols_frame = tk.Frame(main, bg=COLORS["border"], padx=1, pady=1)
        symbols_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 6))
        self.symbols_panel = OutputPanel(symbols_frame)
        self.symbols_panel.pack(fill="both", expand=True)

        # Output panel
        output_frame = tk.Frame(main, bg=COLORS["border"], padx=1, pady=1)
        output_frame.grid(row=1, column=2, sticky="nsew")
        self.output_panel = OutputPanel(output_frame)
        self.output_panel.pack(fill="both", expand=True)

        # Track cursor position
        self.editor.text.bind("<KeyRelease>", self._update_cursor_pos, add="+")
        self.editor.text.bind("<ButtonRelease-1>", self._update_cursor_pos)

    def _build_status_bar(self):
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill="x", side="bottom")

    def _bind_shortcuts(self):
        self.root.bind("<Control-Return>", lambda e: self._compile())
        self.root.bind("<Control-n>", lambda e: self._new_file())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self._save_file_as())

    def _update_cursor_pos(self, _event=None):
        pos = self.editor.text.index("insert")
        line, col = pos.split(".")
        self.status_bar.set_position(line, int(col) + 1)

    # ── Compilation ───────────────────────────────────────────────────────

    def _compile(self):
        source = self.editor.get_content()
        if not source.strip():
            self.status_bar.set_message("Nothing to compile", COLORS["yellow"])
            return

        self.symbols_panel.clear()
        self.output_panel.clear()

        try:
            lexer = Lexer(source)
            emitter = Emitter("out.c")
            parser = Parser(lexer, emitter)
            parser.parse()

            # Symbol table
            symbols_text = self._format_symbol_table(parser)
            self.symbols_panel.set_content(symbols_text)

            # Compiled C output
            c_code = emitter.getOutput()
            self.output_panel.set_content(c_code)

            # Write to file
            emitter.writeFile()

            self.status_bar.set_message("Compilation successful — output saved to out.c",
                                        COLORS["green"])

        except CompilerError as e:
            self.output_panel.set_content(f"Error:\n\n{e}", "red")
            self.status_bar.set_message(f"Compilation failed: {e}", COLORS["red"])

        except Exception as e:
            self.output_panel.set_content(f"Unexpected error:\n\n{e}", "red")
            self.status_bar.set_message("Internal error", COLORS["red"])

    def _format_symbol_table(self, parser):
        lines = []

        lines.append("VARIABLES")
        lines.append("─" * 28)
        if parser.symbols:
            for sym in sorted(parser.symbols):
                lines.append(f"  float  {sym}")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append("LABELS")
        lines.append("─" * 28)
        if parser.labelsDeclared:
            for label in sorted(parser.labelsDeclared):
                lines.append(f"  {label}")
        else:
            lines.append("  (none)")

        return "\n".join(lines)

    # ── File operations ───────────────────────────────────────────────────

    def _new_file(self):
        self.editor.set_content("")
        self.symbols_panel.clear()
        self.output_panel.clear()
        self.current_file = None
        self.status_bar.set_message("New file", COLORS["fg_dim"])

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Open BASIC File",
            filetypes=[("BASIC files", "*.basic *.bas"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.set_content(content)
            self.current_file = path
            self.status_bar.set_message(f"Opened: {os.path.basename(path)}", COLORS["fg_dim"])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def _save_file(self):
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self._save_file_as()

    def _save_file_as(self):
        path = filedialog.asksaveasfilename(
            title="Save BASIC File",
            defaultextension=".basic",
            filetypes=[("BASIC files", "*.basic"), ("All files", "*.*")],
        )
        if not path:
            return
        self.current_file = path
        self._write_file(path)

    def _write_file(self, path):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.editor.get_content())
            self.status_bar.set_message(f"Saved: {os.path.basename(path)}", COLORS["fg_dim"])
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

    def _export_c(self):
        path = filedialog.asksaveasfilename(
            title="Export C Code",
            defaultextension=".c",
            filetypes=[("C files", "*.c"), ("All files", "*.*")],
        )
        if not path:
            return
        c_code = self.output_panel.text.get("1.0", "end-1c")
        if not c_code.strip():
            messagebox.showwarning("Export", "No compiled code to export. Compile first.")
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(c_code)
            self.status_bar.set_message(f"Exported: {os.path.basename(path)}", COLORS["green"])
        except Exception as e:
            messagebox.showerror("Error", f"Could not export:\n{e}")

    # ── Examples ──────────────────────────────────────────────────────────

    def _load_default_example(self):
        """Load calculator example on startup so the user sees something useful."""
        calc = EXAMPLES_DIR / "calculator.basic"
        if calc.exists():
            self._load_example(calc)
        else:
            self.editor.set_content(
                '# Welcome to BASIC-to-C Compiler!\n'
                '# Write your BASIC code here and press Ctrl+Enter to compile.\n\n'
                'PRINT "Hello, World!"\n'
            )

    def _load_example(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.set_content(content)
            self.current_file = None
            name = path.stem.replace("_", " ").title()
            self.status_bar.set_message(f"Loaded example: {name}", COLORS["fg_dim"])
        except Exception as e:
            messagebox.showerror("Error", f"Could not load example:\n{e}")

    # ── Dialogs ───────────────────────────────────────────────────────────

    def _show_lang_ref(self):
        ref = tk.Toplevel(self.root)
        ref.title("BASIC Language Reference")
        ref.geometry("600x520")
        ref.configure(bg=COLORS["bg"])
        ref.transient(self.root)

        text = tk.Text(
            ref, wrap="word", font=FONT_MONO,
            bg=COLORS["bg_panel"], fg=COLORS["fg"],
            relief="flat", padx=16, pady=16,
        )
        text.pack(fill="both", expand=True)

        text.insert("1.0", """BASIC Language Reference
========================

Statements:
  PRINT <expr>          Print a numeric expression
  PRINT "text"          Print a string literal
  INPUT <var>           Read a number from stdin
  LET <var> = <expr>    Assign a value to a variable
  IF <cmp> THEN         Start conditional block
  ENDIF                 End conditional block
  WHILE <cmp> REPEAT    Start loop block
  ENDWHILE              End loop block
  LABEL <name>          Declare a jump target
  GOTO <name>           Jump to a label

Operators:
  +  -  *  /            Arithmetic
  ==  !=                Equality
  <  <=  >  >=          Comparison

Comments:
  # This is a comment   Everything after # is ignored

Variables:
  All variables are float type, auto-declared on first LET or INPUT.

Example:
  LET x = 10
  WHILE x > 0 REPEAT
      PRINT x
      LET x = x - 1
  ENDWHILE
  PRINT "Done!"
""")
        text.configure(state="disabled")

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "BASIC → C  Compiler\n"
            "Version 3.0\n\n"
            "A visual compiler that translates BASIC\n"
            "source code into equivalent C programs.\n\n"
            "Built with Python & Tkinter\n\n"
            "github.com/eoLucasS/Compilador-A3"
        )


def main():
    root = tk.Tk()
    app = CompilerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
