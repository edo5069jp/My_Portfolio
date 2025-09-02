# -*- coding: utf-8 -*-
"""
DirStringSearch v2.6.2（セル青背景 / 依存なし / WinAPIクリップボード / クリック素通し）
- 検索直後の「最初の1クリック」で identify_row/column が空になる場合に対応:
  * 布石: update() と see(先頭行) でレイアウト強制確定 → 再判定
  * それでも空なら、行高と列幅から **近似的にセルを逆算**（即時に青背景を描画）
- 既存のフォールバック描画（行bbox + 列幅）も維持 → 1発目から必ず描画
"""
import os, sys, re, threading, queue, csv, logging, ctypes, time, types
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

APP_NAME = "DirStringSearch"
VERSION = "2.6.2"

def app_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

BASE_DIR = app_base_dir()
LOG_DIR = BASE_DIR / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging
log_path = LOG_DIR / (datetime.now().strftime("%Y%m%d") + ".log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)

ENCODINGS_TRY = ["utf-8", "utf-8-sig", "cp932", "utf-16", "iso-8859-1"]

def read_lines_with_best_effort(path: Path):
    for enc in ENCODINGS_TRY:
        try:
            with path.open("r", encoding=enc, errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    yield i, line.rstrip("\n\r")
            return
        except Exception:
            continue
    try:
        data = path.read_bytes()
        text = data.decode("latin-1", errors="ignore")
        for i, line in enumerate(text.splitlines(), start=1):
            yield i, line
    except Exception:
        return

class SearchWorker(threading.Thread):
    def __init__(self, root_dir, pattern, use_regex, case_sensitive, result_queue, stop_event, logger):
        super().__init__(daemon=True)
        self.root_dir = Path(root_dir)
        self.pattern = pattern
        self.use_regex = use_regex
        self.case_sensitive = case_sensitive
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.logger = logger
        self.total_files = 0
        self.matched = 0
        flags = 0 if case_sensitive else re.IGNORECASE
        self.regex = re.compile(pattern, flags) if use_regex else None

    def file_should_skip(self, p: Path):
        BIN_EXTS = {
            ".exe",".dll",".bin",".jpg",".jpeg",".png",".gif",".webp",".bmp",".ico",
            ".zip",".rar",".7z",".gz",".bz2",".xz",".tar",".pdf",".mp3",".wav",".mp4",".mov",".avi"
        }
        return p.suffix.lower() in BIN_EXTS

    def run(self):
        start_ts = datetime.now()
        logging.info("Search start: root='%s', pattern='%s', regex=%s, case_sensitive=%s",
                     self.root_dir, self.pattern, self.use_regex, self.case_sensitive)
        try:
            for p in self.root_dir.rglob("*"):
                if self.stop_event.is_set():
                    break
                if not p.is_file():
                    continue
                if self.file_should_skip(p):
                    continue
                self.total_files += 1
                try:
                    if self.use_regex:
                        for ln, line in read_lines_with_best_effort(p):
                            if self.stop_event.is_set():
                                break
                            if self.regex.search(line):
                                self.matched += 1
                                self.result_queue.put((str(p), ln, line))
                    else:
                        needle = self.pattern if self.case_sensitive else self.pattern.lower()
                        for ln, line in read_lines_with_best_effort(p):
                            if self.stop_event.is_set():
                                break
                            hay = line if self.case_sensitive else line.lower()
                            if needle in hay:
                                self.matched += 1
                                self.result_queue.put((str(p), ln, line))
                except Exception as e:
                    logging.warning("Failed to scan file: %s (%s)", p, e)
        finally:
            dur = (datetime.now() - start_ts).total_seconds()
            logging.info("Search end: scanned_files=%d, matches=%d, duration_sec=%.2f",
                         self.total_files, self.matched, dur)
            self.result_queue.put(("__DONE__", self.total_files, self.matched))

# ===== Windows Clipboard (CF_UNICODETEXT) 64bit-safe =====
def set_clipboard_text_windows(text: str):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    while text.startswith("\r\n"):
        text = text[2:]
    while text.endswith("\r\n"):
        text = text[:-2]

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    for _ in range(20):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("OpenClipboard failed")

    try:
        if not user32.EmptyClipboard():
            raise RuntimeError("EmptyClipboard failed")

        data = text.encode("utf-16-le") + b"\x00\x00"
        size = len(data)

        hglb = kernel32.GlobalAlloc(0x0002, size)  # GMEM_MOVEABLE
        if not hglb:
            raise MemoryError("GlobalAlloc failed")
        lock = kernel32.GlobalLock(hglb)
        if not lock:
            kernel32.GlobalFree(hglb)
            raise MemoryError("GlobalLock failed")
        try:
            ctypes.memmove(lock, data, size)
        finally:
            kernel32.GlobalUnlock(hglb)

        if not user32.SetClipboardData(13, hglb):  # CF_UNICODETEXT
            kernel32.GlobalFree(hglb)
            raise RuntimeError("SetClipboardData failed")
    finally:
        user32.CloseClipboard()

# ===== Overlay (mouse proxy + fill) =====
class Overlay:
    TRANSPARENT = "#FF00FF"
    FILL_COLOR = "#3390FF"
    TEXT_COLOR = "#FFFFFF"
    PADDING_X = 6

    def __init__(self, tree: ttk.Treeview):
        self.tree = tree
        self.root = tree.winfo_toplevel()

        self.top = tk.Toplevel(self.root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        try:
            self.top.attributes("-transparentcolor", self.TRANSPARENT)
        except tk.TclError:
            self.top.attributes("-alpha", 0.02)  # fallback
        self.top.configure(bg=self.TRANSPARENT)

        self.canvas = tk.Canvas(self.top, bg=self.TRANSPARENT, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        # focus show/hide
        self.root.bind("<FocusIn>", self._focus_in, add="+")
        self.root.bind("<FocusOut>", self._focus_out, add="+")
        self.root.bind("<Unmap>", self._focus_out, add="+")
        self.root.bind("<Map>", self._focus_in, add="+")

        # keep aligned
        self.root.bind("<Configure>", self.sync_geometry, add="+")
        self.tree.bind("<Configure>", self.sync_geometry, add="+")
        self.tree.bind("<Expose>", self.sync_geometry, add="+")

        # mouse proxy callbacks
        self.cb_left = self.cb_drag = self.cb_release = self.cb_right = None
        self.canvas.bind("<Button-1>", self._proxy_left)
        self.canvas.bind("<B1-Motion>", self._proxy_drag)
        self.canvas.bind("<ButtonRelease-1>", self._proxy_release)
        self.canvas.bind("<Button-3>", self._proxy_right)

        self.cells = []
        self.font = self._resolve_font()

        # visible
        self.root.after(10, self._focus_in)

    def set_mouse_proxy(self, left, drag, release, right):
        self.cb_left, self.cb_drag, self.cb_release, self.cb_right = left, drag, release, right

    def _proxy_event(self, e):
        evt = types.SimpleNamespace()
        evt.x, evt.y, evt.state = e.x, e.y, getattr(e, "state", 0)
        return evt

    def _proxy_left(self, e):
        if self.cb_left:
            self.cb_left(self._proxy_event(e))
        return "break"

    def _proxy_drag(self, e):
        if self.cb_drag:
            self.cb_drag(self._proxy_event(e))
        return "break"

    def _proxy_release(self, e):
        if self.cb_release:
            self.cb_release(self._proxy_event(e))
        return "break"

    def _proxy_right(self, e):
        if self.cb_right:
            self.cb_right(self._proxy_event(e))
        return "break"

    def _resolve_font(self):
        style = ttk.Style(self.tree)
        font_name = style.lookup("Treeview", "font")
        if not font_name:
            try:
                return tkfont.nametofont("TkDefaultFont")
            except Exception:
                return ("Segoe UI", 9)
        try:
            return tkfont.nametofont(font_name)
        except Exception:
            return ("Segoe UI", 9)

    def _focus_in(self, event=None):
        try:
            self.top.deiconify()
            self.top.lift()
            self.top.attributes("-topmost", True)
            self.sync_geometry()
        except Exception:
            pass

    def _focus_out(self, event=None):
        try:
            self.top.withdraw()
        except Exception:
            pass

    def sync_geometry(self, event=None):
        try:
            x = self.tree.winfo_rootx()
            y = self.tree.winfo_rooty()
            w = self.tree.winfo_width()
            h = self.tree.winfo_height()
            self.top.geometry(f"{w}x{h}+{x}+{y}")
            self.redraw()
        except Exception:
            pass

    def set_cells(self, cells):
        self.cells = cells or []
        self.redraw()

    def _truncate_to_fit(self, text, width):
        if not text:
            return ""
        if isinstance(self.font, tuple):
            fnt = tkfont.Font(family=self.font[0], size=self.font[1])
        else:
            fnt = self.font
        ellipsis = "…"
        max_w = max(0, width - self.PADDING_X*2)
        if fnt.measure(text) <= max_w:
            return text
        lo, hi = 0, len(text)
        res = ""
        while lo <= hi:
            mid = (lo + hi)//2
            candidate = text[:mid] + ellipsis
            if fnt.measure(candidate) <= max_w:
                res = candidate
                lo = mid + 1
            else:
                hi = mid - 1
        return res

    def redraw(self):
        self.canvas.delete("all")
        if not self.cells:
            return
        for c in self.cells:
            x1,y1,x2,y2 = c["x1"],c["y1"],c["x2"],c["y2"]
            text = c.get("text","")
            anchor = c.get("anchor","w")
            self.canvas.create_rectangle(x1+1, y1+1, x2-1, y2-1, fill=self.FILL_COLOR, outline="")
            disp = self._truncate_to_fit(text, (x2-x1))
            if anchor == "e":
                tx = x2 - self.PADDING_X
                an = "e"
            else:
                tx = x1 + self.PADDING_X
                an = "w"
            ty = y1 + (y2-y1)//2
            self.canvas.create_text(tx, ty, text=disp, fill=self.TEXT_COLOR, font=self.font, anchor=an)

class App(tk.Tk):
    COLS = ("path", "line", "text")

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1100x680")
        self.minsize(900, 560)

        self.dir_var = tk.StringVar(value=str(Path.home()))
        self.pattern_var = tk.StringVar()
        self.regex_var = tk.BooleanVar(value=False)
        self.case_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")
        self.stop_event = threading.Event()
        self.result_queue = queue.Queue()
        self.worker = None

        self.rows = []
        self.iids = []

        self.anchor = None
        self.sel_rect = None
        self.dragging = False

        self.create_widgets()
        self.poll_queue()

    def create_widgets(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill="both", expand=True)

        # Row 1
        r1 = ttk.Frame(frm)
        r1.pack(fill="x", pady=(0,6))
        ttk.Label(r1, text="ディレクトリ:").pack(side="left")
        self.dir_entry = ttk.Entry(r1, textvariable=self.dir_var)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r1, text="参照...", command=self.browse_dir).pack(side="left")

        # Row 2
        r2 = ttk.Frame(frm)
        r2.pack(fill="x", pady=(0,6))
        ttk.Label(r2, text="検索パターン:").pack(side="left")
        self.pattern_entry = ttk.Entry(r2, textvariable=self.pattern_var)
        self.pattern_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Checkbutton(r2, text="正規表現", variable=self.regex_var).pack(side="left", padx=6)
        ttk.Checkbutton(r2, text="大文字小文字を区別", variable=self.case_var).pack(side="left", padx=6)
        ttk.Button(r2, text="検索", command=self.start_search).pack(side="left", padx=(12,0))
        self.stop_btn = ttk.Button(r2, text="停止", command=self.stop_search, state="disabled")
        self.stop_btn.pack(side="left", padx=(6,0))
        ttk.Button(r2, text="CSV出力", command=self.export_csv).pack(side="left", padx=(12,0))

        # Tree
        tree_frame = ttk.Frame(frm)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=self.COLS, show="headings", selectmode="none")
        for col, width, anchor in zip(self.COLS, (520, 80, 480), ("w","e","w")):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=lambda *args: (vsb.set(*args), self.after_idle(self.redraw_selection)))
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Overlay
        self.overlay = Overlay(self.tree)
        self.overlay.set_mouse_proxy(self.on_left_click, self.on_left_drag, self.on_left_release, self.on_right_click)
        self.after(20, self.overlay._focus_in)

        # Events
        self.tree.bind("<Button-1>", self.on_left_click)
        self.tree.bind("<B1-Motion>", self.on_left_drag)
        self.tree.bind("<ButtonRelease-1>", self.on_left_release)
        self.tree.bind("<Double-1>", self.open_selected)
        self.tree.bind("<Configure>", lambda e: self.after_idle(self.redraw_selection))
        self.tree.bind("<MouseWheel>", lambda e: self.after_idle(self.redraw_selection))
        self.bind_all("<Control-c>", self.copy_hotkey)
        self.bind_all("<Control-a>", self.select_all_cells)

        # Context menu
        self.ctx = tk.Menu(self, tearoff=False)
        self.ctx.add_command(label="セルをコピー (Ctrl+C)", command=self.copy_cells)
        self.ctx.add_command(label="選択範囲をコピー", command=self.copy_cells)
        self.ctx.add_separator()
        self.ctx.add_command(label="この行のファイルを開く", command=self.open_row_from_context)
        self.tree.bind("<Button-3>", self.on_right_click)

        # Status bar
        sbar = ttk.Frame(frm)
        sbar.pack(fill="x", pady=(6,0))
        self.status_lbl = ttk.Label(sbar, textvariable=self.status_var, anchor="w")
        self.status_lbl.pack(fill="x")

    # ---- selection ----
    def _column_offsets(self):
        xs, ws, acc = [], [], 0
        for col in self.COLS:
            w = int(self.tree.column(col, "width"))
            xs.append(acc); ws.append(w); acc += w
        return xs, ws

    def _ensure_layout_ready(self):
        self.update_idletasks()
        children = self.tree.get_children("")
        if not children:
            return False
        try:
            self.tree.see(children[0])
        except Exception:
            pass
        self.update()
        return True

    def _row_index_from_iid(self, row_id):
        try:
            return self.iids.index(row_id)
        except ValueError:
            pass
        children = self.tree.get_children("")
        try:
            return children.index(row_id)
        except ValueError:
            return None

    def _approx_cell_from_xy(self, x, y):
        # 行高と列幅から近似セルを推定（最初のクリックでも確実に何か選べる）
        children = self.tree.get_children("")
        if not children:
            return None, None
        # 先頭行の bbox から行のY開始と高さ
        rb = self.tree.bbox(children[0])
        if not rb or rb[3] <= 1:
            return 0, 0
        rx, ry, rw, rh = rb
        if y < ry:
            row_idx = 0
        else:
            row_idx = int((y - ry) // max(1, rh))
            row_idx = max(0, min(row_idx, len(children)-1))
        xs, ws = self._column_offsets()
        col_idx = 0
        cx = 0
        for i, (sx, w) in enumerate(zip(xs, ws)):
            if x < sx + w:
                col_idx = i; break
        else:
            col_idx = len(ws) - 1
        return row_idx, col_idx

    def pos_to_cell(self, x, y):
        self.update_idletasks()
        row_id = self.tree.identify_row(y)
        col_id = self.tree.identify_column(x)
        if not row_id or not col_id or col_id == "#0":
            # レイアウトを確定させ再判定
            if self._ensure_layout_ready():
                row_id = self.tree.identify_row(y) or row_id
                col_id = self.tree.identify_column(x) or col_id
        if not row_id or not col_id or col_id == "#0":
            # それでもダメなら近似で推定
            return self._approx_cell_from_xy(x, y)
        try:
            col_index = int(col_id[1:]) - 1
        except Exception:
            col_index = 0
        row_index = self._row_index_from_iid(row_id)
        if row_index is None:
            # 最後の保険
            return self._approx_cell_from_xy(x, y)
        return row_index, col_index

    def _ensure_overlay_ready(self):
        try:
            self.overlay._focus_in()
            self.overlay.sync_geometry()
            self.update_idletasks()
        except Exception:
            pass

    def _redraw_with_retry(self, tries=12, delay=25):
        painted = self._redraw_once_with_fallback()
        if painted or tries <= 0:
            return
        self.after(delay, lambda: self._redraw_with_retry(tries-1, delay))

    def _redraw_once_with_fallback(self):
        cells = []
        if not self.sel_rect:
            self.overlay.set_cells([])
            return False
        self.update_idletasks()
        r1, c1, r2, c2 = self.sel_rect
        children = self.tree.get_children("")
        if not children:
            self.overlay.set_cells([]); return False
        r1 = max(0, r1); c1 = max(0, c1); r2 = min(len(children)-1, r2); c2 = min(len(self.COLS)-1, c2)
        xs, ws = self._column_offsets()
        any_ok = False
        for ri in range(r1, r2+1):
            iid = children[ri]
            row_bbox = self.tree.bbox(iid)
            for ci in range(c1, c2+1):
                col = f"#{ci+1}"
                bbox = self.tree.bbox(iid, col)
                if bbox and bbox[2] > 2 and bbox[3] > 2:
                    x, y, w, h = bbox
                    any_ok = True
                elif row_bbox and row_bbox[2] > 2 and row_bbox[3] > 2:
                    rx, ry, rw, rh = row_bbox
                    x = rx + xs[ci]; w = ws[ci]; y = ry; h = rh
                    any_ok = True
                else:
                    continue
                vals = self.tree.item(iid, "values")
                txt = str(vals[ci]) if ci < len(vals) else ""
                anc = self.tree.column(self.COLS[ci], "anchor")
                cells.append({"x1": x, "y1": y, "x2": x+w, "y2": y+h, "text": txt, "anchor": anc})
        self.overlay.set_cells(cells)
        return any_ok and bool(cells)

    def on_left_click(self, event):
        self.focus_set()
        self._ensure_overlay_ready()
        r, c = self.pos_to_cell(event.x, event.y)
        if r is None:
            return "break"
        if event.state & 0x0001:  # Shift拡張
            if self.anchor is None:
                self.anchor = (r, c)
            self.sel_rect = (min(self.anchor[0], r), min(self.anchor[1], c),
                             max(self.anchor[0], r), max(self.anchor[1], c))
        else:
            self.anchor = (r, c)
            self.sel_rect = (r, c, r, c)
        self.dragging = True

        try:
            children = self.tree.get_children("")
            if 0 <= r < len(children):
                self.tree.see(children[r])
        except Exception:
            pass

        self._redraw_with_retry()
        return "break"

    def on_left_drag(self, event):
        if not self.dragging or self.anchor is None:
            return "break"
        r, c = self.pos_to_cell(event.x, event.y)
        if r is None:
            return "break"
        self.sel_rect = (min(self.anchor[0], r), min(self.anchor[1], c),
                         max(self.anchor[0], r), max(self.anchor[1], c))
        self._redraw_with_retry()
        return "break"

    def on_left_release(self, event):
        self.dragging = False
        self._redraw_with_retry()
        return "break"

    def select_all_cells(self, event=None):
        if not self.tree.get_children(""):
            return "break"
        self.anchor = (0, 0)
        last_row = len(self.tree.get_children("")) - 1
        self.sel_rect = (0, 0, last_row, len(self.COLS)-1)
        self._redraw_with_retry()
        return "break"

    def redraw_selection(self):
        self._redraw_with_retry(tries=1)

    # ---- copy ----
    def build_tsv_from_selection(self):
        if not self.sel_rect:
            return ""
        r1, c1, r2, c2 = self.sel_rect
        children = self.tree.get_children("")
        r1 = max(0, r1); c1 = max(0, c1); r2 = min(len(children)-1, r2); c2 = min(len(self.COLS)-1, c2)
        pieces = []
        for ri in range(r1, r2+1):
            iid = children[ri]
            vals = self.tree.item(iid, "values")
            picked = [str(vals[ci]) if ci < len(vals) else "" for ci in range(c1, c2+1)]
            picked = [v.replace("\t"," ").replace("\r"," ").replace("\n"," ") for v in picked]
            pieces.append("\t".join(picked))
        return "\r\n".join(pieces)

    def set_clipboard_text(self, text: str):
        if sys.platform.startswith("win"):
            set_clipboard_text_windows(text)
        else:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()

    def copy_cells(self):
        text = self.build_tsv_from_selection()
        if not text:
            self.bell(); return
        try:
            self.set_clipboard_text(text)
            self.status_var.set("コピーしました。")
        except Exception as e:
            messagebox.showerror("エラー", f"コピーに失敗しました:\n{e}")

    def copy_hotkey(self, event=None):
        self.copy_cells()
        return "break"

    # ---- context/open ----
    def on_right_click(self, event):
        self._ensure_overlay_ready()
        r, c = self.pos_to_cell(event.x, event.y)
        if r is not None:
            self.anchor = (r, c)
            self.sel_rect = (r, c, r, c)
            try:
                children = self.tree.get_children("")
                if 0 <= r < len(children):
                    self.tree.see(children[r])
            except Exception:
                pass
            self._redraw_with_retry()
        try:
            self.ctx.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            self.ctx.grab_release()

    def open_row_from_context(self):
        if not self.sel_rect:
            return
        r1, c1, r2, c2 = self.sel_rect
        self.open_row(r1)

    def open_row(self, ri):
        children = self.tree.get_children("")
        if not (0 <= ri < len(children)):
            return
        iid = children[ri]
        vals = self.tree.item(iid, "values")
        path = vals[0] if vals else ""
        if not path:
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開けませんでした:\n{e}")

    def open_selected(self, event=None):
        r, c = self.pos_to_cell(event.x, event.y)
        if r is None:
            if self.sel_rect:
                self.open_row(self.sel_rect[0])
            return
        self.open_row(r)

    # ---- search ----
    def browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get() or str(Path.home()))
        if d:
            self.dir_var.set(d)

    def start_search(self):
        root_dir = self.dir_var.get().strip()
        pattern = self.pattern_var.get()
        if not root_dir or not Path(root_dir).exists():
            messagebox.showerror("エラー", "有効なディレクトリを選択してください。")
            return
        if not pattern:
            messagebox.showerror("エラー", "検索パターンを入力してください。")
            return
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.rows.clear(); self.iids.clear()
        self.sel_rect = None; self.anchor = None
        self.status_var.set("検索中...")
        self.stop_event.clear()
        self.stop_btn.config(state="normal")
        try:
            self.worker = SearchWorker(
                root_dir=root_dir,
                pattern=pattern,
                use_regex=self.regex_var.get(),
                case_sensitive=self.case_var.get(),
                result_queue=self.result_queue,
                stop_event=self.stop_event,
                logger=logging.getLogger(APP_NAME)
            )
            self.worker.start()
        except re.error as e:
            messagebox.showerror("正規表現エラー", str(e))
            self.status_var.set("正規表現エラー: " + str(e))
            self.stop_btn.config(state="disabled")

    def stop_search(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.status_var.set("停止中...")
            self.stop_btn.config(state="disabled")

    def poll_queue(self):
        try:
            updated = False
            while True:
                item = self.result_queue.get_nowait()
                if item[0] == "__DONE__":
                    total, matched = item[1], item[2]
                    self.status_var.set(f"完了: ファイル数 {total:,} 件 / ヒット {matched:,} 件")
                    self.stop_btn.config(state="disabled")
                    self.worker = None
                    break
                else:
                    path, ln, text = item
                    if len(text) > 200:
                        text = text[:200] + "…"
                    self.rows.append([path, ln, text])
                    iid = self.tree.insert("", "end", values=(path, ln, text))
                    self.iids.append(iid)
                    updated = True
            if updated:
                self.update_idletasks()
                self.after_idle(self.redraw_selection)
        except queue.Empty:
            pass
        self.after(60, self.poll_queue)

    def export_csv(self):
        if not self.rows:
            messagebox.showinfo("情報", "結果がありません。")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default = f"search_result_{ts}.csv"
        fpath = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default,
                                             filetypes=[("CSV", "*.csv"), ("All Files", "*.*")])
        if not fpath:
            return
        try:
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["path", "line", "text"])
                w.writerows(self.rows)
            messagebox.showinfo("成功", "CSVを書き出しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"CSVを書き出せませんでした:\n{e}")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
