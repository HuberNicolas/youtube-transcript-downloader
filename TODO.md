# TODO

Open tasks. See also [Known issues](README.md#known-issues).

## 1. Modernise

- [x] Move from a script with hard-coded IDs to the `yt-transcript` command in the package
      `src/youtube_transcript_downloader`
- [x] Use uv, youtube-transcript-api 1.2 and Python 3.12+
- [x] Read list files, accept all common URL forms, add output formats and a language fallback
- [x] Test a real run on a list of 20 videos (20 downloaded)
- [ ] Add tests for `extract_video_id` and `read_sources`
- [ ] Optional: translate transcripts with `--translate LANG`

## 2. Publish

- [x] Add the MIT License
- [x] Keep downloaded transcripts and personal video lists out of the repository (`data/`, `transcripts/`)
- [x] Make the repository public
