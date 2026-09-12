import json
import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from song_parser import parse_file
from youtube_search import SearchResult
from batch_processor import BatchProcessor, ProcessingItem, ItemStatus, BatchStats
from ffmpeg_setup import find_ffmpeg, download_ffmpeg

APP_TITLE = "Mp3Swift"
CONFIG_FILE = "config.json"


def load_config() -> dict:
    defaults = {
        "output_dir": "output",
        "ffmpeg_dir": "ffmpeg",
        "confidence_threshold": 60,
        "max_results_per_search": 5,
        "audio_format": "mp3",
        "audio_quality": "192",
        "log_file": "ytmusicbatch.log",
        "report_file": "report.txt",
        "max_retries": 2,
        "retry_delay_seconds": 3,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_cfg = json.load(f)
            defaults.update(user_cfg)
        except Exception:
            pass
    return defaults


def setup_logging(log_file: str):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding='utf-8',
    )


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("900x600")

        self.config = load_config()
        setup_logging(self.config["log_file"])

        self.processor: BatchProcessor | None = None
        self.txt_path = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self):
        # Top frame - file selection
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="Playlist file:").pack(side=tk.LEFT)

        self.path_entry = tk.Entry(top_frame, width=50)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.path_entry.configure(textvariable=self.txt_path, state="readonly")

        tk.Button(top_frame, text="Browse", command=self._select_file).pack(side=tk.LEFT)

        # Middle frame - buttons
        btn_frame = tk.Frame(self.root, pady=5)
        btn_frame.pack(fill=tk.X)

        self.btn_search = tk.Button(btn_frame, text="Search", width=12, command=self._search)
        self.btn_search.pack(side=tk.LEFT, padx=5)

        self.btn_start = tk.Button(btn_frame, text="Download", width=12, command=self._start)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_pause = tk.Button(btn_frame, text="Pause", width=12, command=self._pause)
        self.btn_pause.pack(side=tk.LEFT, padx=5)
        self.btn_pause.config(state=tk.DISABLED)

        self.btn_cancel = tk.Button(btn_frame, text="Cancel", width=12, command=self._cancel)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        self.btn_cancel.config(state=tk.DISABLED)

        tk.Button(btn_frame, text="Open Output", command=self._open_output).pack(side=tk.LEFT, padx=20)

        # Table
        table_frame = tk.Frame(self.root, padx=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("#", "Song", "Artist", "Result", "Score", "Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)

        for col in cols:
            self.tree.heading(col, text=col)

        self.tree.column("#", width=40)
        self.tree.column("Song", width=200)
        self.tree.column("Artist", width=150)
        self.tree.column("Result", width=250)
        self.tree.column("Score", width=60)
        self.tree.column("Status", width=80)

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom frame - progress
        bottom_frame = tk.Frame(self.root, padx=10, pady=10)
        bottom_frame.pack(fill=tk.X)

        self.progress_bar = ttk.Progressbar(bottom_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X)

        self.status_label = tk.Label(bottom_frame, textvariable=self.status_text, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(5, 0))

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Select song list",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.txt_path.set(path)
            self.status_text.set(f"Loaded: {os.path.basename(path)}")

    def _search(self):
        path = self.txt_path.get()
        if not path or not os.path.exists(path):
            messagebox.showwarning(APP_TITLE, "Please select a valid .txt file first.")
            return

        entries = parse_file(path)
        if not entries:
            messagebox.showinfo(APP_TITLE, "No song entries found in the file.")
            return

        self.processor = BatchProcessor(self.config)
        self.processor.set_entries(entries)

        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(self.processor.items, 1):
            artist_str = ", ".join(item.entry.artists) if item.entry.artists else ""
            self.tree.insert("", tk.END, iid=str(i), values=(
                i, item.entry.title, artist_str, "", "", "Pending"
            ))

        self.progress_bar["maximum"] = len(self.processor.items)
        self.progress_bar["value"] = 0
        self.status_text.set("Searching...")
        self.btn_search.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.DISABLED)

        def run_search():
            self.processor.on_item_update = self._on_item_update_threadsafe
            self.processor.search_all()
            self.root.after(0, self._search_done)

        threading.Thread(target=run_search, daemon=True).start()

    def _on_item_update_threadsafe(self, item: ProcessingItem):
        self.root.after(0, lambda: self._update_row(item))

    def _update_row(self, item: ProcessingItem):
        idx = self.processor.items.index(item) + 1
        iid = str(idx)
        artist_str = ", ".join(item.entry.artists) if item.entry.artists else ""
        result_str = item.best_result.title if item.best_result else ""
        score_str = f"{item.best_result.score}%" if item.best_result else ""
        status = item.status.value

        self.tree.item(iid, values=(
            idx, item.entry.title, artist_str, result_str, score_str, status
        ))
        self.progress_bar["value"] = idx

    def _search_done(self):
        total = len(self.processor.items)
        self.status_text.set(f"Found {total} songs - Ready to download")
        self.progress_bar["value"] = 0
        self.btn_start.config(state=tk.NORMAL)
        self.btn_search.config(state=tk.NORMAL)

    def _start(self):
        if not self.processor:
            return

        ffmpeg_path = find_ffmpeg(self.config["ffmpeg_dir"])
        if not ffmpeg_path:
            self.status_text.set("Downloading FFmpeg...")
            self.btn_start.config(state=tk.DISABLED)

            def get_ffmpeg():
                path = download_ffmpeg(
                    self.config["ffmpeg_dir"],
                    progress_callback=lambda msg: self.root.after(0, lambda: self.status_text.set(msg))
                )
                if path:
                    self.processor.ffmpeg_dir = path
                    self.root.after(0, self._run_processing)
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        APP_TITLE, "Could not download FFmpeg. Install it manually."
                    ))
                    self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))

            threading.Thread(target=get_ffmpeg, daemon=True).start()
            return

        self.processor.ffmpeg_dir = ffmpeg_path
        self._run_processing()

    def _run_processing(self):
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.NORMAL)

        total = len(self.processor.items)
        self.progress_bar["maximum"] = total if total > 0 else 1
        self.progress_bar["value"] = 0

        def on_progress(index, stats: BatchStats):
            self.root.after(0, lambda: self._update_progress(stats))

        def on_item_update(item):
            self.root.after(0, lambda: self._update_row(item))

        def on_complete(stats):
            self.root.after(0, lambda: self._processing_done(stats))

        self.processor.on_progress = on_progress
        self.processor.on_item_update = on_item_update
        self.processor.on_complete = on_complete

        threading.Thread(target=self.processor.process_all, daemon=True).start()

    def _update_progress(self, stats: BatchStats):
        self.progress_bar["value"] = stats.processed
        self.status_text.set(
            f"{stats.processed}/{stats.total}  Success: {stats.success}  Failed: {stats.failed}  Skipped: {stats.skipped}"
        )

    def _processing_done(self, stats: BatchStats):
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.DISABLED)
        self.status_text.set("Complete!")

        report_path = self.config.get("report_file", "report.txt")
        report = self.processor.generate_report(report_path)
        messagebox.showinfo(APP_TITLE, f"Complete!\n\nSuccess: {stats.success}\nFailed: {stats.failed}\nSkipped: {stats.skipped}")

    def _pause(self):
        if self.processor:
            if self.processor.is_paused:
                self.processor.resume()
                self.btn_pause.config(text="Pause")
                self.status_text.set("Downloading...")
            else:
                self.processor.pause()
                self.btn_pause.config(text="Resume")
                self.status_text.set("Paused")

    def _cancel(self):
        if self.processor:
            self.processor.cancel()
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_cancel.config(state=tk.DISABLED)
            self.status_text.set("Cancelled")

    def _open_output(self):
        output = os.path.abspath(self.config["output_dir"])
        os.makedirs(output, exist_ok=True)
        os.startfile(output)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()