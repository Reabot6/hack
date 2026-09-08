import whisper
import os
from pathlib import Path

from services.ffmpeg import FFMPEG

_model = None


def _ensure_ffmpeg_on_path() -> None:
    """Make the FFmpeg binary used by our converter available to Whisper too."""
    ffmpeg_dir = str(Path(FFMPEG).parent)
    if not Path(FFMPEG).is_file():
        raise RuntimeError(f"FFmpeg executable was not found at {FFMPEG}")

    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if ffmpeg_dir not in path_entries:
        os.environ["PATH"] = os.pathsep.join([ffmpeg_dir, *path_entries])

def get_model():
    global _model
    if _model is None:
        print("[Whisper] Loading model... (first time downloads ~150MB)")
        _model = whisper.load_model("base")
        print("[Whisper] Model ready")
    return _model

def transcribe(audio_path: str) -> dict:
    try:
        _ensure_ffmpeg_on_path()
        model = get_model()
        result = model.transcribe(audio_path)
        segments = []
        if "segments" in result:
            segments = [
                {
                    "start": round(s["start"], 2),
                    "end": round(s["end"], 2),
                    "text": s["text"].strip(),
                }
                for s in result["segments"]
            ]
        print(f"[DEBUG] Whisper done. Text length: {len(result['text'])} Segments: {len(segments)}")
        return {
            "text": result["text"].strip(),
            "segments": segments,
        }
    except Exception as e:
        raise RuntimeError(f"Whisper transcription failed: {str(e)}")

def format_srt(segments: list) -> str:
    srt_lines = []
    for i, seg in enumerate(segments, start=1):
        start = _seconds_to_srt_time(seg["start"])
        end = _seconds_to_srt_time(seg["end"])
        srt_lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
    return "\n".join(srt_lines)

def _seconds_to_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
