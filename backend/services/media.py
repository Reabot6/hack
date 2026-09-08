import subprocess
from pathlib import Path

from services.ffmpeg import FFMPEG
from services.whisper import format_srt


MEDIA_DIR = Path(__file__).parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def source_path(video_id: str) -> Path | None:
    matches = list(MEDIA_DIR.glob(f"{video_id}_source.*"))
    return matches[0] if matches else None


def clip_path(video_id: str, clip_id: str) -> Path:
    return MEDIA_DIR / f"{video_id}_clip_{clip_id}.mp4"


def render_vertical_clip(video_id: str, clip_id: str, start: float, end: float, segments: list) -> Path:
    """Render a vertical MP4 and burn in the relevant transcript captions."""
    source = source_path(video_id)
    if not source:
        raise RuntimeError("The original source file is unavailable. Re-upload the video to render a clip.")
    if source.suffix.lower() not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        raise RuntimeError("Clips can only be rendered from a video upload, not an audio-only file.")

    output = clip_path(video_id, clip_id)
    subtitle = output.with_suffix(".srt")
    relevant = []
    for segment in segments:
        if segment.get("end", 0) >= start and segment.get("start", 0) <= end:
            relevant.append({
                "start": max(0, segment["start"] - start),
                "end": min(end - start, segment["end"] - start),
                "text": segment["text"],
            })
    subtitle.write_text(format_srt(relevant), encoding="utf-8")

    # A centered 9:16 crop is predictable for a fast MVP. The source transcript
    # is supplied to FFmpeg's subtitles filter so the render is ready to post.
    escaped_subtitle = str(subtitle.resolve()).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    video_filter = (
        "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
        "scale=1080:1920,"
        f"subtitles='{escaped_subtitle}':force_style='Alignment=2,Fontsize=20,Outline=2'"
    )
    try:
        subprocess.run(
            [FFMPEG, "-y", "-ss", str(start), "-to", str(end), "-i", str(source),
             "-vf", video_filter, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
             "-c:a", "aac", "-movflags", "+faststart", str(output)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Clip render failed: {exc.stderr.decode(errors='replace')[-500:]}") from exc
    return output
