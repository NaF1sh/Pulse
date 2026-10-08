"""Normalize player artwork and derive YouTube thumbnails from known video URLs."""
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit


def artwork_url(artwork, track_url=None):
    if isinstance(artwork, str) and len(artwork) <= 2048:
        artwork = artwork.strip()
        if artwork.startswith("/") and not artwork.startswith("//"):
            return Path(artwork).as_uri()
        try:
            url = urlsplit(artwork)
            if (not url.username and not url.password
                    and ((url.scheme in ("https", "http") and url.hostname)
                         or (url.scheme == "file" and url.netloc in ("", "localhost") and url.path))):
                return artwork
        except ValueError:
            pass
    if not isinstance(track_url, str) or len(track_url) > 2048:
        return ""
    try:
        url = urlsplit(track_url)
        if url.scheme not in ("https", "http") or url.username or url.password:
            return ""
        video = ""
        if url.hostname == "youtu.be":
            video = url.path.strip("/").split("/")[0]
        elif url.hostname in ("youtube.com", "www.youtube.com", "music.youtube.com", "m.youtube.com"):
            if url.path == "/watch":
                video = parse_qs(url.query).get("v", [""])[0]
            else:
                parts = url.path.strip("/").split("/")
                if len(parts) == 2 and parts[0] in ("shorts", "embed", "live"):
                    video = parts[1]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video):
            return f"https://i.ytimg.com/vi/{video}/hqdefault.jpg"
    except ValueError:
        pass
    return ""
