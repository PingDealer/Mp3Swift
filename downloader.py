import logging
import os
import subprocess
import shutil

logger = logging.getLogger(__name__)


def _find_yt_dlp() -> str | None:
    """Find yt-dlp executable or module, checking Windows .exe extension and Python module."""
    if shutil.which("yt-dlp"):
        return "yt-dlp"
    if shutil.which("yt-dlp.exe"):
        return "yt-dlp.exe"
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
        logger.error("yt-dlp not found in PATH")
        return []

    # If it's just "python", use module mode
    if yt_dlp_path == "python":
        return ["python", "-m", "yt_dlp"]

    return [yt_dlp_path]


def download_and_convert(
    url: str,
    output_path: str,
    ffmpeg_dir: str | None = None,
    audio_quality: str = "192",
    yt_dlp_path: str | None = None,
) -> bool:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Get the command to run yt-dlp
    cmd = _get_yt_dlp_command(yt_dlp_path)
    if not cmd:
        return False

    cmd.extend([
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", audio_quality,
        "-o", output_path,
        "--no-playlist",
        "--quiet",
        "--no-warnings",
    ])

    if ffmpeg_dir and os.path.isdir(ffmpeg_dir):
        cmd.extend(["--ffmpeg-location", ffmpeg_dir])

    cmd.append(url)

    logger.info(f"Downloading: {url} -> {output_path}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, encoding='utf-8'
        )
    except FileNotFoundError:
        logger.error(f"yt-dlp command not found: {' '.join(cmd[:2])}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Download timed out for {url}")
        return False

    if result.returncode != 0:
        logger.error(f"Download failed: {result.stderr[:500]}")
        return False

    expected_mp3 = output_path if output_path.endswith('.mp3') else output_path + '.mp3'
    if not os.path.exists(output_path) and os.path.exists(expected_mp3):
        pass
    elif not os.path.exists(output_path):
        for ext in ['.mp3', '.m4a', '.webm', '.opus']:
            alt = output_path.rsplit('.', 1)[0] + ext if '.' in output_path else output_path + ext
            if os.path.exists(alt):
                logger.info(f"Found output at {alt}")
                return True
        logger.error(f"Output file not found after download: {output_path}")
        return False

    return True
