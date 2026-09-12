import io
import logging
import os
import shutil
import zipfile
import urllib.request

logger = logging.getLogger(__name__)

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def find_ffmpeg(ffmpeg_dir: str) -> str | None:
    if shutil.which("ffmpeg"):
        return os.path.dirname(shutil.which("ffmpeg"))

    bin_path = os.path.join(ffmpeg_dir, "bin", "ffmpeg.exe")
    if os.path.exists(bin_path):
        return os.path.join(ffmpeg_dir, "bin")

    for root, dirs, files in os.walk(ffmpeg_dir):
        if "ffmpeg.exe" in files:
            return root

    return None


def download_ffmpeg(ffmpeg_dir: str, progress_callback=None) -> str | None:
    existing = find_ffmpeg(ffmpeg_dir)
    if existing:
        logger.info(f"FFmpeg already available at: {existing}")
        return existing

    os.makedirs(ffmpeg_dir, exist_ok=True)
    zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")

    logger.info("Downloading FFmpeg...")
    if progress_callback:
        progress_callback("Downloading FFmpeg (this may take a minute)...")

    try:
        urllib.request.urlretrieve(FFMPEG_URL, zip_path)
    except Exception as e:
        logger.error(f"Failed to download FFmpeg: {e}")
        if progress_callback:
            progress_callback(f"FFmpeg download failed: {e}")
        return None

    logger.info("Extracting FFmpeg...")
    if progress_callback:
        progress_callback("Extracting FFmpeg...")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(ffmpeg_dir)
    except Exception as e:
        logger.error(f"Failed to extract FFmpeg: {e}")
        return None
    finally:
        try:
            os.remove(zip_path)
        except OSError:
            pass

    result = find_ffmpeg(ffmpeg_dir)
    if result:
        logger.info(f"FFmpeg ready at: {result}")
        if progress_callback:
            progress_callback("FFmpeg ready.")
    else:
        logger.error("FFmpeg not found after extraction")
        if progress_callback:
            progress_callback("FFmpeg extraction failed — ffmpeg.exe not found.")

    return result
