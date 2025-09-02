# -*- coding: utf-8 -*-
# movable_capture_box.py
# JP UI / 録音元を単一選択（なし / システム音 / マイク）
# soundcardで安定ループバック / 最初のフレームで自動ch決定
# 連写OK / メニュー閉で終了 / 設定閉で終了しない / 影なし

import sys
import os
import json
import time
import threading
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import numpy as np
import cv2
from mss import mss

import soundfile as sf
import soundcard as sc  # 安定WASAPIループバック

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QRect, QPoint

APP_NAME = "MovableCaptureBox"
CONFIG_NAME = "movable_capture_config.json"
DEFAULT_FPS = 30

# ----------------- 共通ユーティリティ -----------------
def default_output_dir() -> Path:
    pics = Path.home() / "Pictures"
    out = pics / "Captures"
    out.mkdir(parents=True, exist_ok=True)
    return out

def find_ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")

# ----------------- オーディオ列挙（表示名） -----------------
def list_loopback_names() -> List[str]:
    try:
        return [sp.name for sp in sc.all_speakers()]
    except Exception:
        return []

def list_mic_names() -> List[str]:
    try:
        return [m.name for m in sc.all_microphones()]
    except Exception:
        return []

# ----------------- 設定（録音元は1項目） -----------------
# audio_source: 'none' / 'loop:auto' / 'loop:name::<device_name>' / 'mic:auto' / 'mic:name::<device_name>'
def load_config(config_path: Path):
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            out_dir = Path(data.get("output_dir", str(default_output_dir())))
            fps = int(data.get("fps", DEFAULT_FPS))
            audio_source = data.get("audio_source", "loop:auto")
            out_dir.mkdir(parents=True, exist_ok=True)
            return out_dir, fps, audio_source
        except Exception:
            pass
    return default_output_dir(), DEFAULT_FPS, "loop:auto"

def save_config(config_path: Path, out_dir: Path, fps: int, audio_source: str):
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({
                "output_dir": str(out_dir),
                "fps": int(fps),
                "audio_source": str(audio_source),
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def parse_audio_source(src: str):
    # 戻り値: (mode, device_name or None)  mode: 'none'|'loop'|'mic'
    if not src or src == "loop:auto": return ("loop", None)
    if src == "none":                 return ("none", None)
    if src == "mic:auto":             return ("mic",  None)
    if src.startswith("loop:name::"): return ("loop", src.split("loop:name::",1)[1] or None)
    if src.startswith("mic:name::"):  return ("mic",  src.split("mic:name::",1)[1] or None)
    if src.startswith("loop:"):       return ("loop", None)  # 旧互換
    if src.startswith("mic:"):        return ("mic",  None)
    return ("loop", None)

# ----------------- 録画ワーカ -----------------
class RecordingWorker(QtCore.QThread):
    finished = QtCore.Signal(str, bool)  # (video_path, ok)

    def __init__(self, region_rect: QRect, out_path: Path, fps: int, parent=None):
        super().__init__(parent)
        self.region = QRect(region_rect)
        self.out_path = out_path
        self.fps = max(1, int(fps))
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        w, h = self.region.width(), self.region.height()
        if w <= 1 or h <= 1:
            self.finished.emit(str(self.out_path), False)
            return
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        sct = mss()
        frame_interval = 1.0 / float(self.fps)
        ok = True
        writer = None
        try:
            writer = cv2.VideoWriter(str(self.out_path), fourcc, float(self.fps), (w, h))
            if not writer.isOpened():
                ok = False
                raise RuntimeError("VideoWriter open failed")

            mon = {"left": int(self.region.left()), "top": int(self.region.top()),
                   "width": int(w), "height": int(h)}

            next_time = time.perf_counter()
            while not self._stop_event.is_set():
                img = sct.grab(mon)  # BGRA
                frame = np.array(img)[..., :3]  # BGR
                if frame.shape[1] != w or frame.shape[0] != h:
                    frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
                writer.write(frame)

                next_time += frame_interval
                sleep_dur = next_time - time.perf_counter()
                if sleep_dur > 0:
                    time.sleep(sleep_dur)
        except Exception:
            ok = False
        finally:
            try:
                if writer is not None:
                    writer.release()
            except Exception:
                ok = False
            self.finished.emit(str(self.out_path), ok)

# ----------------- オーディオ録音（soundcard） -----------------
class AudioRecorder(QtCore.QThread):
    finished = QtCore.Signal(str, bool)  # (audio_path, ok)

    def __init__(self, audio_source: str, out_wav: Path, parent=None):
        super().__init__(parent)
        self.audio_source = audio_source
        self.out_wav = out_wav
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def _open_loopback_mic(self, name: Optional[str]):
        # ループバックは「マイク」として取得するのが互換的
        try:
            target = name or sc.default_speaker().name
        except Exception:
            target = None
        mic = None
        try:
            mic = sc.get_microphone(target, include_loopback=True)
        except Exception:
            pass
        if mic is None:
            # 最悪、既定マイクで代替（無音になる可能性あり）
            mic = sc.default_microphone()
        return mic

    def _open_mic(self, name: Optional[str]):
        try:
            return sc.get_microphone(name) if name else sc.default_microphone()
        except Exception:
            return sc.default_microphone()

    def run(self):
        mode, name = parse_audio_source(self.audio_source)
        if mode == "none":
            self.finished.emit("", True)
            return

        # レートは48k→44.1kの順でトライ
        sr_candidates = [48000, 44100]
        ok = False
        last_err = None

        for sr in sr_candidates:
            try:
                if mode == "loop":
                    mic = self._open_loopback_mic(name)
                else:
                    mic = self._open_mic(name)

                frames = int(sr * 0.1)
                # channels はオープン後の最初のフレームで自動決定
                with mic.recorder(samplerate=sr) as rec:
                    wav = None
                    print(f"[INFO] Audio start ({'system' if mode=='loop' else 'mic'}): name={mic.name}, sr={sr}")
                    while not self._stop.is_set():
                        data = rec.record(numframes=frames)  # (n, ch) のfloat32
                        if data is None:
                            continue
                        if wav is None:
                            ch = 1 if (data.ndim == 1) else int(data.shape[1])
                            wav = sf.SoundFile(str(self.out_wav), mode="w",
                                               samplerate=sr, channels=ch, subtype="PCM_16")
                        wav.write(data)
                    if wav is not None:
                        wav.close()
                ok = True
                break
            except Exception as e:
                last_err = e
                continue

        if not ok:
            print(f"[ERROR] オーディオ初期化/録音に失敗: {last_err}")
        self.finished.emit(str(self.out_wav) if ok else "", ok)

# ----------------- 設定ダイアログ -----------------
class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, out_dir: Path, fps: int, audio_source: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.resize(560, 240)

        self.loop_names = list_loopback_names()
        self.mic_names  = list_mic_names()

        # ---- 保存先 ----
        self.dir_edit = QtWidgets.QLineEdit(str(out_dir))
        browse_btn = QtWidgets.QPushButton("参照...")
        browse_btn.clicked.connect(self.browse)
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)

        # ---- FPS ----
        self.fps_spin = QtWidgets.QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(int(fps))

        # ---- 録音元（単一コンボ）----
        self.audio_combo = QtWidgets.QComboBox()
        self._audio_keys: List[str] = []

        def add(label: str, key: str):
            self.audio_combo.addItem(label); self._audio_keys.append(key)

        add("なし", "none")
        add("システム音（自動）", "loop:auto")
        for n in self.loop_names:
            add(f"システム音：{n}", f"loop:name::{n}")
        add("マイク（自動）", "mic:auto")
        for n in self.mic_names:
            add(f"マイク：{n}", f"mic:name::{n}")

        cur = audio_source if audio_source in self._audio_keys else "loop:auto"
        try:
            idx = self._audio_keys.index(cur)
        except ValueError:
            idx = self._audio_keys.index("loop:auto")
        self.audio_combo.setCurrentIndex(idx)

        # ---- ボタン ----
        btn_ok = QtWidgets.QPushButton("OK")
        btn_cancel = QtWidgets.QPushButton("キャンセル")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        form = QtWidgets.QFormLayout()
        form.addRow("保存先ディレクトリ:", dir_layout)
        form.addRow("フレームレート (FPS):", self.fps_spin)
        form.addRow("録音元:", self.audio_combo)

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)

        base = QtWidgets.QVBoxLayout(self)
        base.addLayout(form)
        base.addStretch()
        base.addLayout(btns)

    def browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "保存先フォルダを選択")
        if d: self.dir_edit.setText(d)

    def values(self):
        key = self._audio_keys[self.audio_combo.currentIndex()]
        return Path(self.dir_edit.text()), int(self.fps_spin.value()), key

# ----------------- UI（パネル/枠/アプリ） -----------------
class ControlPanel(QtWidgets.QWidget):
    request_shot = QtCore.Signal()
    request_toggle_rec = QtCore.Signal()
    request_open_settings = QtCore.Signal()
    closing = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("キャプチャ操作")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedHeight(56)

        self.btn_shot = QtWidgets.QPushButton("静止画（F9）")
        self.btn_rec = QtWidgets.QPushButton("録画開始（F10）")
        self.btn_set = QtWidgets.QPushButton("設定（Ctrl+O）")

        for b in (self.btn_shot, self.btn_rec, self.btn_set):
            b.setCursor(Qt.PointingHandCursor)

        self.btn_shot.clicked.connect(self.request_shot.emit)
        self.btn_rec.clicked.connect(self.request_toggle_rec.emit)
        self.btn_set.clicked.connect(self.request_open_settings.emit)

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)
        lay.addWidget(self.btn_shot)
        lay.addWidget(self.btn_rec)
        lay.addWidget(self.btn_set)

    def set_recording(self, recording: bool):
        self.btn_rec.setText("録画停止（F10）" if recording else "録画開始（F10）")

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self.closing.emit()
        return super().closeEvent(e)

class CaptureFrame(QtWidgets.QWidget):
    border_color = QtGui.QColor(0, 153, 255, 220)
    fill_shade   = QtGui.QColor(0, 153, 255, 40)
    handle_size  = 8
    min_w        = 40
    min_h        = 40
    NONE, MOVE, LEFT, RIGHT, TOP, BOTTOM, TOPLEFT, TOPRIGHT, BOTTOMLEFT, BOTTOMRIGHT = range(10)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("キャプチャ枠")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setMouseTracking(True)

        # 影は使わない（透明レイヤ＋影のWin不具合回避）

        screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        w, h = int(screen.width() * 0.3), int(screen.height() * 0.3)
        x, y = screen.center().x() - w // 2, screen.center().y() - h // 2
        self.setGeometry(x, y, w, h)

        self._drag_pos = QPoint()
        self._resizing = self.NONE
        self._orig_geo = QRect()

    def paintEvent(self, _):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        r = self.rect()
        p.fillRect(r, self.fill_shade)
        p.setPen(QtGui.QPen(self.border_color, 2))
        p.drawRect(r.adjusted(1, 1, -1, -1))
        s = self.handle_size
        for pt in self._handle_points(r):
            p.fillRect(QtCore.QRect(pt.x()-s//2, pt.y()-s//2, s, s), self.border_color)

    def _handle_points(self, r: QRect):
        cx, cy = r.center().x(), r.center().y()
        return [
            QPoint(r.left(), cy), QPoint(r.right(), cy),
            QPoint(cx, r.top()),  QPoint(cx, r.bottom()),
            QPoint(r.left(), r.top()), QPoint(r.right(), r.top()),
            QPoint(r.left(), r.bottom()), QPoint(r.right(), r.bottom()),
        ]

    def _hit_test(self, pos: QPoint):
        r = self.rect()
        s = self.handle_size
        corners = {
            self.TOPLEFT: QtCore.QRect(r.left()-s//2, r.top()-s//2, s, s),
            self.TOPRIGHT: QtCore.QRect(r.right()-s//2, r.top()-s//2, s, s),
            self.BOTTOMLEFT: QtCore.QRect(r.left()-s//2, r.bottom()-s//2, s, s),
            self.BOTTOMRIGHT: QtCore.QRect(r.right()-s//2, r.bottom()-s//2, s, s),
        }
        for kind, rr in corners.items():
            if rr.contains(pos): return kind
        m = self.handle_size
        if abs(pos.x() - r.left()) <= m:   return self.LEFT
        if abs(pos.x() - r.right()) <= m:  return self.RIGHT
        if abs(pos.y() - r.top()) <= m:    return self.TOP
        if abs(pos.y() - r.bottom()) <= m: return self.BOTTOM
        if r.contains(pos):                return self.MOVE
        return self.NONE

    def mousePressEvent(self, e: QtGui.QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._resizing = self._hit_test(e.position().toPoint())
            self._drag_pos = e.globalPosition().toPoint()
            self._orig_geo = self.geometry()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        pos = e.position().toPoint()
        kind = self._hit_test(pos)
        cursor_map = {
            self.MOVE: Qt.SizeAllCursor, self.LEFT: Qt.SizeHorCursor, self.RIGHT: Qt.SizeHorCursor,
            self.TOP: Qt.SizeVerCursor,  self.BOTTOM: Qt.SizeVerCursor,
            self.TOPLEFT: Qt.SizeFDiagCursor, self.BOTTOMRIGHT: Qt.SizeFDiagCursor,
            self.TOPRIGHT: Qt.SizeBDiagCursor, self.BOTTOMLEFT: Qt.SizeBDiagCursor, self.NONE: Qt.ArrowCursor}
        self.setCursor(cursor_map.get(kind, Qt.ArrowCursor))

        if e.buttons() & Qt.LeftButton and self._resizing is not self.NONE:
            delta = e.globalPosition().toPoint() - self._drag_pos
            geo = QRect(self._orig_geo)
            if self._resizing == self.MOVE:
                geo.moveTo(self._orig_geo.topLeft() + delta)
            else:
                if self._resizing in (self.LEFT, self.TOPLEFT, self.BOTTOMLEFT):
                    new_left = self._orig_geo.left() + delta.x()
                    if self._orig_geo.right() - new_left + 1 >= self.min_w: geo.setLeft(new_left)
                if self._resizing in (self.RIGHT, self.TOPRIGHT, self.BOTTOMRIGHT):
                    new_right = self._orig_geo.right() + delta.x()
                    if new_right - self._orig_geo.left() + 1 >= self.min_w: geo.setRight(new_right)
                if self._resizing in (self.TOP, self.TOPLEFT, self.TOPRIGHT):
                    new_top = self._orig_geo.top() + delta.y()
                    if self._orig_geo.bottom() - new_top + 1 >= self.min_h: geo.setTop(new_top)
                if self._resizing in (self.BOTTOM, self.BOTTOMLEFT, self.BOTTOMRIGHT):
                    new_bottom = self._orig_geo.bottom() + delta.y()
                    if new_bottom - self._orig_geo.top() + 1 >= self.min_h: geo.setBottom(new_bottom)
            self.setGeometry(geo)

    def mouseReleaseEvent(self, _): self._resizing = self.NONE
    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if e.key() == Qt.Key_Escape:
            QtWidgets.QApplication.quit()
    def region_rect_global(self) -> QRect:
        return self.frameGeometry()

# ----------------- アプリ -----------------
class MainApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        QtCore.QCoreApplication.setOrganizationName(APP_NAME)
        # High DPIポリシーの静的設定は行わない（作成後に触るとエラー）

        self.setQuitOnLastWindowClosed(False)

        self.config_path = Path(__file__).with_name(CONFIG_NAME)
        self.output_dir, self.fps, self.audio_source = load_config(self.config_path)

        self.frame = CaptureFrame()
        self.panel = ControlPanel()
        self.panel.request_shot.connect(self.capture_image)
        self.panel.request_toggle_rec.connect(self.toggle_recording)
        self.panel.request_open_settings.connect(self.open_settings)
        self.panel.closing.connect(self.quit_app)  # メニュー×で終了

        for host in (self.frame, self.panel):
            QtGui.QShortcut(QtGui.QKeySequence("F9"), host, activated=self.capture_image)
            QtGui.QShortcut(QtGui.QKeySequence("F10"), host, activated=self.toggle_recording)
            QtGui.QShortcut(QtGui.QKeySequence("Ctrl+O"), host, activated=self.open_settings)

        self.frame.show()
        pf = self.frame.frameGeometry()
        self.panel.move(pf.right() + 20, pf.top())
        self.panel.show()

        self.recording = False
        self.worker: Optional[RecordingWorker] = None
        self.audio: Optional[AudioRecorder] = None
        self._video_done_path: Optional[str] = None
        self._audio_done_path: Optional[str] = None

    def _timestamp(self): return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _hide_ui_for_still(self):
        self.panel.hide(); self.frame.hide()
        QtWidgets.QApplication.processEvents()
        time.sleep(0.06)

    def _show_ui(self):
        self.frame.show(); self.panel.show()
        QtWidgets.QApplication.processEvents()

    # ---- 静止画 ----
    def capture_image(self):
        rect = self.frame.region_rect_global()
        if rect.width() <= 1 or rect.height() <= 1:
            print("[ERROR] キャプチャ領域が小さすぎます。"); return
        self._hide_ui_for_still()
        try:
            mon = {"left": int(rect.left()), "top": int(rect.top()),
                   "width": int(rect.width()), "height": int(rect.height())}
            with mss() as sct:
                img = sct.grab(mon)
                arr = np.array(img)[:, :, :3]
                fn = self.output_dir / f"capture_{self._timestamp()}.png"
                cv2.imwrite(str(fn), arr)
                print(f"[OK] 静止画保存: {fn}")
        finally:
            self._show_ui()

    # ---- 録画 ----
    def toggle_recording(self):
        if not self.recording:
            rect = self.frame.region_rect_global()
            if rect.width() <= 1 or rect.height() <= 1:
                print("[ERROR] キャプチャ領域が小さすぎます。"); return

            video_path = self.output_dir / f"record_{self._timestamp()}.mp4"
            self.panel.set_recording(True)
            self._video_done_path = None; self._audio_done_path = None

            mode, _ = parse_audio_source(self.audio_source)
            if mode != "none":
                audio_wav = video_path.with_suffix(".wav")
                self.audio = AudioRecorder(self.audio_source, audio_wav, self)
                self.audio.finished.connect(self._on_audio_finished)
                self.audio.start()
                time.sleep(0.03)

            self.frame.hide(); QtWidgets.QApplication.processEvents()
            self.worker = RecordingWorker(rect, video_path, self.fps, self)
            self.worker.finished.connect(self._on_video_finished)
            self.worker.start()
            self.recording = True
        else:
            if self.worker and self.worker.isRunning(): self.worker.stop()
            if self.audio and self.audio.isRunning():   self.audio.stop()

    def _on_video_finished(self, out_path: str, ok: bool):
        self._video_done_path = out_path if ok else None
        if parse_audio_source(self.audio_source)[0] == "none": self._finalize_record()
        else: self._finish_if_ready()

    def _on_audio_finished(self, out_path: str, ok: bool):
        self._audio_done_path = out_path if ok else None
        self._finish_if_ready()

    def _finish_if_ready(self):
        if not self.recording: return
        if parse_audio_source(self.audio_source)[0] == "none": return
        if (self._video_done_path is not None) and (self._audio_done_path is not None):
            self._finalize_record()

    def _finalize_record(self):
        self.recording = False
        self.worker = None; self.audio = None
        self.frame.show(); self.panel.set_recording(False)
        QtWidgets.QApplication.processEvents()

        v = self._video_done_path; a = self._audio_done_path
        if v is None:
            print("[ERROR] 動画の保存に失敗しました。"); return
        if parse_audio_source(self.audio_source)[0] == "none" or a is None:
            print(f"[OK] 動画保存: {v}"); return

        ff = find_ffmpeg()
        if ff:
            mux_out = Path(v).with_suffix(".mux.mp4")
            cmd = [ff, "-y", "-i", v, "-i", a, "-c:v", "copy", "-c:a", "aac", "-shortest", str(mux_out)]
            try:
                subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                try: os.replace(str(mux_out), str(v))
                except Exception: print(f"[INFO] 置き換え失敗、mux出力を残します: {mux_out}")
                try: os.remove(a)
                except Exception: pass
                print(f"[OK] 映像+音声 保存: {v}")
            except Exception as e:
                print(f"[WARN] ffmpeg結合に失敗。映像MP4と音声WAVを別々に保存します。 error={e}")
                print(f"[OK] 映像: {v}"); print(f"[OK] 音声: {a}")
        else:
            print("[INFO] ffmpeg 未検出のため、映像MP4と音声WAVを別々に保存します。")
            print(f"[OK] 映像: {v}"); print(f"[OK] 音声: {a}")

    # ---- 設定 ----
    def open_settings(self):
        dlg = SettingsDialog(self.output_dir, self.fps, self.audio_source, parent=self.panel)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            out_dir, fps, audio_source = dlg.values()
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"[ERROR] フォルダを作成できませんでした: {e}")
                return
            self.output_dir = out_dir
            self.fps = int(fps)
            self.audio_source = audio_source
            save_config(self.config_path, self.output_dir, self.fps, self.audio_source)

    # ---- 終了（メニュー×で呼ばれる）----
    def quit_app(self):
        try:
            if getattr(self, "worker", None) and self.worker.isRunning():
                self.worker.stop()
        except Exception: pass
        try:
            if getattr(self, "audio", None) and self.audio.isRunning():
                self.audio.stop()
        except Exception: pass
        try:
            if getattr(self, "worker", None): self.worker.wait(5000)
        except Exception: pass
        try:
            if getattr(self, "audio", None): self.audio.wait(5000)
        except Exception: pass
        try:
            if self.recording: self._finalize_record()
        except Exception: pass
        try:
            if getattr(self, "frame", None): self.frame.close()
        except Exception: pass
        try:
            if getattr(self, "panel", None): self.panel.close()
        except Exception: pass
        print("[INFO] アプリを終了します。")
        self.quit()

# ----------------- エントリポイント -----------------
def main():
    app = MainApp(sys.argv)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
