import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum

from song_parser import SongEntry
from youtube_search import SearchResult, search_youtube
from downloader import download_and_convert

logger = logging.getLogger(__name__)


class ItemStatus(Enum):
    PENDING = "Pending"
    SEARCHING = "Searching"
    MATCHED = "Matched"
    UNCERTAIN = "Uncertain"
    DOWNLOADING = "Downloading"
    SUCCESS = "Success"
    FAILED = "Failed"
    SKIPPED = "Skipped"


@dataclass
class ProcessingItem:
    entry: SongEntry
    status: ItemStatus = ItemStatus.PENDING
    best_result: SearchResult | None = None
    all_results: list[SearchResult] = field(default_factory=list)
    output_file: str = ""
    error: str = ""


@dataclass
class BatchStats:
    total: int = 0
    processed: int = 0
    success: int = 0
    failed: int = 0
    uncertain: int = 0
    skipped: int = 0


class BatchProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.items: list[ProcessingItem] = []
        self.stats = BatchStats()
        self._paused = False
        self._cancelled = False
        self.output_dir = config.get("output_dir", "output")
        self.ffmpeg_dir = config.get("ffmpeg_dir", "ffmpeg")
        self.threshold = config.get("confidence_threshold", 60)
        self.max_results = config.get("max_results_per_search", 5)
        self.audio_quality = str(config.get("audio_quality", "192"))
        self.max_retries = config.get("max_retries", 2)
        self.retry_delay = config.get("retry_delay_seconds", 3)

        self.on_progress = None
        self.on_item_update = None
        self.on_complete = None
        self._selected_indices: set[int] | None = None

    def set_entries(self, entries: list[SongEntry]):
        seen_titles = set()
        self.items = []
        for entry in entries:
            key = entry.title.lower().strip()
            if key in seen_titles:
                item = ProcessingItem(entry=entry, status=ItemStatus.SKIPPED)
                item.error = "Duplicate"
                self.items.append(item)
            else:
                seen_titles.add(key)
                self.items.append(ProcessingItem(entry=entry))
        self.stats = BatchStats(total=len(self.items))

    def set_selected_indices(self, selected: set[int]):
        """Set which item indices (1-based) should be downloaded. None = all matched."""
        self._selected_indices = selected

    def search_all(self):
        for item in self.items:
            if self._cancelled:
                break
            if item.status == ItemStatus.SKIPPED:
                self.stats.skipped += 1
                continue
            self._search_item(item)
            if self.on_item_update:
                self.on_item_update(item)

    def _search_item(self, item: ProcessingItem):
        item.status = ItemStatus.SEARCHING
        if self.on_item_update:
            self.on_item_update(item)

        query = item.entry.search_query
        logger.info(f"Searching for: {query}")
        results = search_youtube(query, self.max_results)
        item.all_results = results

        if not results:
            item.status = ItemStatus.FAILED
            item.error = "No search results (check logs for yt-dlp errors)"
            logger.error(f"Search returned no results for: {query}")
            return

        best = results[0]
        item.best_result = best
        logger.info(f"Best match for '{query}': {best.title} (score: {best.score}%)")

        if best.score >= self.threshold:
            item.status = ItemStatus.MATCHED
        else:
            item.status = ItemStatus.UNCERTAIN
            self.stats.uncertain += 1

    def process_all(self):
        os.makedirs(self.output_dir, exist_ok=True)

        for i, item in enumerate(self.items):
            if self._cancelled:
                break
            while self._paused:
                time.sleep(0.3)
                if self._cancelled:
                    break

            # Process all items that have a best result
            if not item.best_result:
                self.stats.processed += 1
                self._notify_progress(i)
                continue

            self._process_item(item)
            self.stats.processed += 1
            self._notify_progress(i)

        if self.on_complete:
            self.on_complete(self.stats)

    def _process_item(self, item: ProcessingItem):
        item.status = ItemStatus.DOWNLOADING
        if self.on_item_update:
            self.on_item_update(item)

        filename = item.entry.clean_filename + ".mp3"
        output_path = os.path.join(self.output_dir, filename)

        if os.path.exists(output_path):
            item.status = ItemStatus.SKIPPED
            item.output_file = output_path
            item.error = "File already exists"
            self.stats.skipped += 1
            return

        for attempt in range(1, self.max_retries + 1):
            success = download_and_convert(
                url=item.best_result.url,
                output_path=output_path,
                ffmpeg_dir=self.ffmpeg_dir,
                audio_quality=self.audio_quality,
            )
            if success:
                item.status = ItemStatus.SUCCESS
                item.output_file = output_path
                self.stats.success += 1
                return
            if attempt < self.max_retries:
                logger.warning(f"Retry {attempt}/{self.max_retries} for {item.entry.title}")
                time.sleep(self.retry_delay)

        item.status = ItemStatus.FAILED
        item.error = "Download/conversion failed after retries"
        self.stats.failed += 1

    def _notify_progress(self, index: int):
        if self.on_progress:
            self.on_progress(index + 1, self.stats)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def cancel(self):
        self._cancelled = True
        self._paused = False

    @property
    def is_paused(self):
        return self._paused

    def generate_report(self, report_path: str | None = None):
        path = report_path or self.config.get("report_file", "report.txt")
        lines = []
        lines.append("=" * 60)
        lines.append("Mp3Swift — Processing Report")
        lines.append("=" * 60)
        lines.append("")

        # SUCCESS
        lines.append("SUCCESS")
        lines.append("-" * 40)
        success_items = [it for it in self.items if it.status == ItemStatus.SUCCESS]
        if success_items:
            for it in success_items:
                lines.append(f"  Song:   {it.entry.title}")
                lines.append(f"  Result: {it.best_result.title if it.best_result else 'N/A'}")
                lines.append(f"  URL:    {it.best_result.url if it.best_result else 'N/A'}")
                lines.append(f"  File:   {it.output_file}")
                lines.append("")
        else:
            lines.append("  (none)")
            lines.append("")

        # FAILED
        lines.append("FAILED")
        lines.append("-" * 40)
        failed_items = [it for it in self.items if it.status == ItemStatus.FAILED]
        if failed_items:
            for it in failed_items:
                lines.append(f"  Song:   {it.entry.title}")
                lines.append(f"  Reason: {it.error}")
                lines.append("")
        else:
            lines.append("  (none)")
            lines.append("")

        # UNCERTAIN
        lines.append("UNCERTAIN")
        lines.append("-" * 40)
        uncertain_items = [it for it in self.items if it.status == ItemStatus.UNCERTAIN]
        if uncertain_items:
            for it in uncertain_items:
                lines.append(f"  Song: {it.entry.title}")
                lines.append(f"  Candidates:")
                for r in it.all_results[:5]:
                    lines.append(f"    - [{r.score}%] {r.title} ({r.channel}) {r.url}")
                lines.append("")
        else:
            lines.append("  (none)")
            lines.append("")

        # SKIPPED
        skipped_items = [it for it in self.items if it.status == ItemStatus.SKIPPED]
        if skipped_items:
            lines.append("SKIPPED")
            lines.append("-" * 40)
            for it in skipped_items:
                lines.append(f"  Song:   {it.entry.title}")
                lines.append(f"  Reason: {it.error}")
                lines.append("")

        # SUMMARY
        lines.append("=" * 60)
        lines.append(f"Total: {self.stats.total}  |  Success: {self.stats.success}  |  "
                      f"Failed: {self.stats.failed}  |  Uncertain: {self.stats.uncertain}  |  "
                      f"Skipped: {self.stats.skipped}")
        lines.append("=" * 60)

        report_text = "\n".join(lines)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        logger.info(f"Report saved to {path}")
        return report_text
