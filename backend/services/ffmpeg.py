import subprocess
import os
import shutil
from pathlib import Path

# Local development can keep using the Windows install, while Docker/hosting
# environments use the system binary (or an explicit FFMPEG_PATH).
FFMPEG = (
    os.getenv("FFMPEG_PATH")
    or shutil.which("ffmpeg")
    or r"C:\Users\HomePC\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
)


def _ffmpeg_binary() -> str:
    if not Path(FFMPEG).is_file():
        raise RuntimeError("FFmpeg is not installed. Install it on the server or set FFMPEG_PATH.")
    return FFMPEG


def extract_audio(input_path: str, output_path: str) -> str:
    try:
        subprocess.run(
            [_ffmpeg_binary(), "-i", str(input_path), "-vn", "-acodec", "mp3", "-b:a", "64k", "-y", str(output_path)],
            check=True,
            capture_output=True,
        )
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")


def compress_audio(input_path: str, output_path: str) -> str:
    try:
        subprocess.run(
            [_ffmpeg_binary(), "-i", str(input_path), "-acodec", "mp3", "-b:a", "64k", "-y", str(output_path)],
            check=True,
            capture_output=True,
        )
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")


def is_video_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def is_audio_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".mp3", ".wav", ".m4a", ".aac", ".ogg"}


def get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)
