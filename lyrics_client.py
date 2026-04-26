import os
import re
import requests


LYRICS_DIR = "lyrics"


def safe_filename(name: str) -> str:
    """
    Chuyển tên bài/nghệ sĩ thành tên file an toàn trên Windows.
    """
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip()
    return name


def build_lrc_path(track_name: str, artist_name: str) -> str:
    os.makedirs(LYRICS_DIR, exist_ok=True)

    filename = safe_filename(f"{artist_name} - {track_name}.lrc")
    return os.path.join(LYRICS_DIR, filename)


def get_lrc_from_local(track_name: str, artist_name: str):
    path = build_lrc_path(track_name, artist_name)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_lrc_to_local(track_name: str, artist_name: str, lrc_text: str):
    path = build_lrc_path(track_name, artist_name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(lrc_text)

    return path


def fetch_lrc_from_lrclib(
    track_name: str,
    artist_name: str,
    album_name=None,
    duration_seconds=None
):
    """
    Gọi LRCLIB để lấy synced lyrics.
    Nếu không có syncedLyrics thì trả về None.
    """
    url = "https://lrclib.net/api/search"

    params = {
        "track_name": track_name,
        "artist_name": artist_name
    }

    if album_name:
        params["album_name"] = album_name

    if duration_seconds:
        params["duration"] = int(duration_seconds)

    response = requests.get(
        url,
        params=params,
        timeout=10,
        headers={
            "User-Agent": "SpotifyLyricsOverlay/1.0"
        }
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    # Ưu tiên kết quả có syncedLyrics
    for item in results:
        synced = item.get("syncedLyrics")
        if synced:
            return synced

    return None


def get_or_download_lrc(
    track_name: str,
    artist_name: str,
    album_name=None,
    duration_seconds=None
):
    """
    1. Kiểm tra file local.
    2. Nếu chưa có thì gọi LRCLIB.
    3. Nếu lấy được thì lưu lại.
    """
    local_lrc = get_lrc_from_local(track_name, artist_name)

    if local_lrc:
        print("Đã tìm thấy lyrics trong máy.")
        return local_lrc

    print("Chưa có lyrics local, đang gọi LRCLIB...")

    lrc = fetch_lrc_from_lrclib(
        track_name=track_name,
        artist_name=artist_name,
        album_name=album_name,
        duration_seconds=duration_seconds
    )

    if not lrc:
        print("Không tìm thấy synced lyrics trên LRCLIB.")
        return None

    path = save_lrc_to_local(track_name, artist_name, lrc)
    print(f"Đã lưu lyrics vào: {path}")

    return lrc