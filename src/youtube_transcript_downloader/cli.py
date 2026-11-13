"""Command-line interface."""

import argparse
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

from youtube_transcript_downloader.downloader import FORMATTERS, download, read_sources


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="yt-transcript",
        description="Download the transcripts of YouTube videos.",
    )
    parser.add_argument("videos", nargs="*", help="video URLs or IDs")
    parser.add_argument(
        "-f", "--file", type=Path, action="append", default=[], help="file with one URL or ID per line (repeatable)"
    )
    parser.add_argument(
        "-o", "--out", type=Path, default=Path("transcripts"), help="output folder (default: %(default)s)"
    )
    parser.add_argument(
        "-l",
        "--lang",
        type=lambda value: [code.strip() for code in value.split(",") if code.strip()],
        default=["de", "en"],
        help="preferred languages in order, comma-separated (default: de,en)",
    )
    parser.add_argument("--format", choices=FORMATTERS, default="txt", help="output format (default: %(default)s)")
    parser.add_argument("--strict", action="store_true", help="fail instead of falling back to another language")
    args = parser.parse_args(argv)
    if not args.videos and not args.file:
        parser.error("give at least one video URL or ID, or a file with --file")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ids = read_sources(args.videos, args.file)
    api = YouTubeTranscriptApi()
    failed = 0
    for i, video_id in enumerate(ids, 1):
        try:
            path = download(video_id, args.out, args.lang, args.format, api, args.strict)
            print(f"[{i}/{len(ids)}] {video_id} -> {path}")
        except Exception as e:  # the library raises many different errors
            failed += 1
            first_line = str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__
            print(f"[{i}/{len(ids)}] {video_id} failed: {type(e).__name__}: {first_line}")
    print(f"Done: {len(ids) - failed} downloaded, {failed} failed.")
    return 1 if failed else 0
