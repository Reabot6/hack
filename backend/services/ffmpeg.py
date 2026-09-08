import subprocess
import os
from pathlib import Path

FFMPEG = r"C:\Users\HomePC\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"


def extract_audio(input_path: str, output_path: str) -> str:
    try:
        subprocess.run(
            [FFMPEG, "-i", str(input_path), "-vn", "-acodec", "mp3", "-b:a", "64k", "-y", str(output_path)],
            check=True,
            capture_output=True,
        )
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")


def compress_audio(input_path: str, output_path: str) -> str:
    try:
        subprocess.run(
            [FFMPEG, "-i", str(input_path), "-acodec", "mp3", "-b:a", "64k", "-y", str(output_path)],
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