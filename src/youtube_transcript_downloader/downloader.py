"""Find video IDs and download transcripts."""

import re
from pathlib import Path

from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter, SRTFormatter, TextFormatter, WebVTTFormatter
from yt_dlp import YoutubeDL

FORMATTERS = {
    "txt": TextFormatter,
    "json": JSONFormatter,
    "srt": SRTFormatter,
    "vtt": WebVTTFormatter,
}

_ID = r"[A-Za-z0-9_-]{11}"
_PATTERNS = [
    re.compile(rf"(?:v=|youtu\.be/|/shorts/|/embed/|/live/|/v/)({_ID})"),
    re.compile(rf"^({_ID})$"),
]


_PLAYLIST = re.compile(r"(?:[?&]list=|^)((?:PL|OL|UU|FL|RD)[A-Za-z0-9_-]{10,})")


def extract_playlist_id(text: str) -> str | None:
    """Return the playlist ID in a URL (list=...) or bare playlist ID, or None."""
    match = _PLAYLIST.search(text.strip().strip(",;"))
    return match.group(1) if match else None


class _Silent:
    """yt-dlp logger that prints nothing; errors are raised and reported by the caller."""

    def debug(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...


def playlist_video_ids(playlist_id: str) -> list[str]:
    """Return the IDs of all videos in a playlist, using yt-dlp without downloading any video."""
    options = {"extract_flat": True, "quiet": True, "no_warnings": True, "skip_download": True, "logger": _Silent()}
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/playlist?list={playlist_id}", download=False)
    return [entry["id"] for entry in info.get("entries") or [] if entry and entry.get("id")]


def extract_video_id(text: str) -> str | None:
    """Return the video ID in a URL or bare ID, or None."""
    text = text.strip().strip(",;")
    for pattern in _PATTERNS:
        if match := pattern.search(text):
            return match.group(1)
    return None


def read_sources(items: list[str], files: list[Path]) -> list[str]:
    """Collect unique video IDs from arguments and from list files (one URL or ID per line).

    Playlist URLs and IDs are expanded to all their videos.
    """
    lines = list(items)
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0]
            lines.extend(part for part in re.split(r"[\s,]+", line) if part)

    ids: list[str] = []
    for line in lines:
        if playlist_id := extract_playlist_id(line):
            try:
                found = playlist_video_ids(playlist_id)
                print(f"Playlist {playlist_id}: {len(found)} videos")
            except Exception as e:  # yt-dlp raises DownloadError for private or missing playlists
                print(f"Skipped playlist {playlist_id}: {e}")
                continue
            ids.extend(video_id for video_id in found if video_id not in ids)
            continue
        video_id = extract_video_id(line)
        if video_id is None:
            print(f"Skipped, no video ID found: {line}")
        elif video_id not in ids:
            ids.append(video_id)
    return ids


def download(
    video_id: str,
    out_dir: Path,
    languages: list[str],
    fmt: str = "txt",
    api: YouTubeTranscriptApi | None = None,
    strict: bool = False,
) -> Path:
    """Download one transcript and write it to out_dir. Return the path of the file.

    Without strict, fall back to any available language if none of `languages` exists.
    """
    api = api or YouTubeTranscriptApi()
    try:
        transcript = api.fetch(video_id, languages=languages)
    except NoTranscriptFound:
        if strict:
            raise
        # None of the preferred languages: take the first transcript the video has.
        transcript = next(iter(api.list(video_id))).fetch()
    text = FORMATTERS[fmt]().format_transcript(transcript)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{video_id}.{transcript.language_code}.{fmt}"
    path.write_text(text + "\n", encoding="utf-8")
    return path
