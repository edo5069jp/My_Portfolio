# -*- coding: utf-8 -*-
import os, sys, re, threading, queue, csv, logging
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "DirStringSearch"
VERSION = "1.0.0"

def app_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

BASE_DIR = app_base_dir()
LOG_DIR = BASE_DIR / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
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
                    yield i, line.rstrip("\\n\\r")
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
        if p.suffix.lower() in BIN_EXTS:
            return True
        return False

    def run(self):
        start_ts = datetime.now()
        self.logger.info(f"Search start: root='{self.root_dir}', pattern='{self.pattern}', regex={self.use_regex}, case_sensitive={self.case_sensitive}")
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
                    self.logger.warning(f"Failed to scan file: {p} ({e})")
        finally:
            dur = (datetime.now() - start_ts).total_seconds()
            self.logger.info(f"Search end: scanned_files={self.total_files}, matches={self.matched}, duration_sec={dur:.2f}")
            self.result_queue.put(("__DONE__", self.total_files, self.matched))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("980x640")
        self.minsize(800, 520)

        self.dir_var = tk.StringVar(value=str(Path.home()))
        self.pattern_var = tk.StringVar()
        self.regex_var = tk.BooleanVar(value=False)
        self.case_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")
        self.stop_event = threading.Event()
        self.result_queue = queue.Queue()
        self.worker = None

        self.create_widgets()
        self.poll_queue()

    def create_widgets(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill="both", expand=True)

        r1 = ttk.Frame(frm)
        r1.pack(fill="x", pady=(0,6))
        ttk.Label(r1, text="ディレクトリ:").pack(side="left")
        self.dir_entry = ttk.Entry(r1, textvariable=self.dir_var)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r1, text="参照...", command=self.browse_dir).pack(side="left")

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

        cols = ("path", "line", "text")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=20)
        self.tree.heading("path", text="ファイルパス")
        self.tree.heading("line", text="行")
        self.tree.heading("text", text="スニペット")
        self.tree.column("path", width=420, anchor="w")
        self.tree.column("line", width=60, anchor="e")
        self.tree.column("text", width=420, anchor="w")
        self.tree.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.open_selected)

        sbar = ttk.Frame(frm)
        sbar.pack(fill="x", pady=(6,0))
        self.status_lbl = ttk.Label(sbar, textvariable=self.status_var, anchor="w")
        self.status_lbl.pack(fill="x")

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
        for i in self.tree.get_children():
            self.tree.delete(i)
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
                    self.tree.insert("", "end", values=(path, ln, text))
        except queue.Empty:
            pass
        self.after(50, self.poll_queue)

    def open_selected(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.tree.item(sel[0], "values")[0]
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開けませんでした:\\n{e}")

    def export_csv(self):
        if not self.tree.get_children():
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
                for iid in self.tree.get_children():
                    w.writerow(self.tree.item(iid, "values"))
            messagebox.showinfo("成功", "CSVを書き出しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"CSVを書き出せませんでした:\\n{e}")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
