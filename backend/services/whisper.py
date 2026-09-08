import os
from openai import OpenAI

MAX_FILE_SIZE_MB = 24  # Whisper limit is 25MB, keep buffer

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def transcribe(audio_path: str) -> dict:
    """
    Transcribe audio file using Whisper API.
    Returns dict with:
      - text: full transcript string
      - segments: list of {start, end, text} dicts with timestamps
    Raises RuntimeError on failure.
    """
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise RuntimeError(
            f"Audio file is {file_size_mb:.1f}MB. "
            f"Maximum is {MAX_FILE_SIZE_MB}MB. "
            "Try uploading a shorter video or audio-only file."
        )

    try:
        with open(audio_path, "rb") as f:
            response = get_client().audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        if hasattr(response, "segments") and response.segments:
            segments = [
                {
                    "start": round(s.start, 2),
                    "end": round(s.end, 2),
                    "text": s.text.strip(),
                }
                for s in response.segments
            ]

        return {
            "text": response.text.strip(),
            "segments": segments,
        }

    except Exception as e:
        raise RuntimeError(f"Whisper transcription failed: {str(e)}")


def format_srt(segments: list) -> str:
    """
    Convert timestamped segments to .srt caption format.
    """
    srt_lines = []
    for i, seg in enumerate(segments, start=1):
        start = _seconds_to_srt_time(seg["start"])
        end = _seconds_to_srt_time(seg["end"])
        srt_lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
    return "\n".join(srt_lines)


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert float seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
