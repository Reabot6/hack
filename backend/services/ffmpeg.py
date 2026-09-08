import subprocess
import os
from pathlib import Path


def extract_audio(input_path: str, output_path: str) -> str:
    """
    Extract audio from MP4 and compress to 64kbps MP3.
    Returns output_path on success.
    Raises RuntimeError on failure.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_path,
                "-vn",           # no video stream
                "-acodec", "mp3",
                "-b:a", "64k",   # compress — keeps under Whisper 25MB limit
                "-y",            # overwrite output if exists
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg audio extraction failed: {e.stderr.decode()}")


def compress_audio(input_path: str, output_path: str) -> str:
    """
    Compress existing audio file to 64kbps MP3.
    Used when upload is already audio but may be large.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_path,
                "-acodec", "mp3",
                "-b:a", "64k",
                "-y",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg compression failed: {e.stderr.decode()}")


def is_video_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def is_audio_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".mp3", ".wav", ".m4a", ".aac", ".ogg"}


def get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)
