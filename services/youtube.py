import re
from urllib.parse import urlparse, parse_qs

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def parse_video_id(url: str) -> str:
    """YouTube URL formatlaridan 11 belgili video ID ajratadi."""

    raw = url.strip()

    if not raw:
        raise ValueError("YouTube havolasi bo‘sh")

    candidate = None

    # URL sxemasi bo‘lmasa ham youtube.com/... formatini qabul qilamiz.
    parsed = urlparse(
        raw if "://" in raw else "https://" + raw
    )

    host = parsed.netloc.lower().removeprefix("www.")
    path = [part for part in parsed.path.split("/") if part]

    if host in {
        "youtu.be",
        "m.youtube.com",
        "youtube.com",
        "music.youtube.com"
    }:
        if host == "youtu.be" and path:
            candidate = path[0]

        elif parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [None])[0]

        elif len(path) >= 2 and path[0] in {
            "embed",
            "shorts",
            "live",
            "v"
        }:
            candidate = path[1]

    if not candidate or not VIDEO_ID.fullmatch(candidate):
        raise ValueError(
            "YouTube havolasi noto‘g‘ri yoki video ID aniqlanmadi"
        )

    return candidate
