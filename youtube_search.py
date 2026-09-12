import logging
import subprocess
import json
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    channel: str
    duration: str
    score: int


def _fuzzy_word_match(word_a: str, word_b: str) -> bool:
    if word_a == word_b:
        return True
    if len(word_a) < 3 or len(word_b) < 3:
        return False
    if word_a in word_b or word_b in word_a:
        return True
    shorter, longer = (word_a, word_b) if len(word_a) <= len(word_b) else (word_b, word_a)
    if len(shorter) >= 4 and shorter[:4] == longer[:4]:
        return True
    return False


def _count_fuzzy_matches(query_words: set[str], target_words: set[str]) -> int:
    matched = 0
    used = set()
    for qw in query_words:
        for tw in target_words:
            if tw not in used and _fuzzy_word_match(qw, tw):
                matched += 1
                used.add(tw)
                break
    return matched


def _compute_score(query: str, result_title: str, result_channel: str) -> int:
    query_lower = query.lower()
    title_lower = result_title.lower()
    channel_lower = result_channel.lower()

    query_words = set(query_lower.split())
    title_words = set(title_lower.split())

    if not query_words:
        return 0

    matched = _count_fuzzy_matches(query_words, title_words)
    word_score = int((matched / len(query_words)) * 65)

    channel_words = set(channel_lower.split())
    combined = title_words | channel_words
    combined_matched = _count_fuzzy_matches(query_words, combined)
    combined_score = int((combined_matched / len(query_words)) * 70)
    word_score = max(word_score, combined_score)

    penalty = 0
    noise = ['karaoke', 'cover', 'remix', 'live', 'concert', 'instrumental', 'slowed', 'reverb', 'reaction']
    for word in noise:
        if word in title_lower and word not in query_lower:
            penalty += 10

    bonus = 0
    if 'official' in title_lower or 'audio' in title_lower:
        bonus += 5
    if 'topic' in channel_lower:
        bonus += 10

    return max(0, min(100, word_score + bonus - penalty))


def _find_yt_dlp() -> str | None:
    """Find yt-dlp executable or module, checking Windows .exe extension and Python module."""
    import shutil
    # Try direct executable first
    if shutil.which("yt-dlp"):
        return "yt-dlp"
    if shutil.which("yt-dlp.exe"):
        return "yt-dlp.exe"
    # On Windows, try yt-dlp.exe explicitly
    if os.name == 'nt' and shutil.which("yt-dlp.exe"):
        return "yt-dlp.exe"
    # Try Python module approach (python -m yt_dlp)
    try:
        import yt_dlp
        if yt_dlp:
            return "python"
    except ImportError:
        pass
    return None


def _get_yt_dlp_command(yt_dlp_path: str | None = None) -> list[str]:
    """Get the command list to run yt-dlp."""
    if yt_dlp_path is None:
        yt_dlp_path = _find_yt_dlp()

    if yt_dlp_path is None:
        logger.error("yt-dlp not found in PATH. Please install yt-dlp: pip install yt-dlp")
        return []

    # If it's just "python", use module mode
    if yt_dlp_path == "python":
        return ["python", "-m", "yt_dlp"]

    return [yt_dlp_path]


def search_youtube(query: str, max_results: int = 5, yt_dlp_path: str | None = None) -> list[SearchResult]:
    # Get the command to run yt-dlp
    cmd = _get_yt_dlp_command(yt_dlp_path)
    if not cmd:
        return []

    cmd.extend([
        f"ytsearch{max_results}:{query}",
        "--dump-json",
        "--no-download",
        "--flat-playlist",
        "--quiet",
        "--no-warnings",
    ])

    logger.info(f"Searching YouTube: {query}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60, encoding='utf-8'
        )
    except FileNotFoundError:
        logger.error(f"yt-dlp command not found: {' '.join(cmd[:2])}")
        return []
    except subprocess.TimeoutExpired:
        logger.error("YouTube search timed out")
        return []

    if result.returncode != 0:
        logger.error(f"yt-dlp search failed (code {result.returncode}): {result.stderr[:500]}")
        return []

    if not result.stdout.strip():
        logger.warning(f"No search results returned for query: {query}")
        return []

    results = []
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        url = data.get('url') or data.get('webpage_url') or f"https://www.youtube.com/watch?v={data.get('id', '')}"
        duration_secs = data.get('duration') or 0
        if duration_secs:
            mins, secs = divmod(int(duration_secs), 60)
            duration_str = f"{mins}:{secs:02d}"
        else:
            duration_str = "?"

        title = data.get('title', 'Unknown')
        channel = data.get('channel', '') or data.get('uploader', '') or ''

        score = _compute_score(query, title, channel)
        results.append(SearchResult(
            title=title,
            url=url,
            channel=channel,
            duration=duration_str,
            score=score,
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results
