import time
import os
from dotenv import load_dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from lyrics_client import get_or_download_lrc
from lrc_parser import parse_lrc, get_current_lyric


load_dotenv()

SCOPE = "user-read-currently-playing"


def ms_to_time(ms):
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def create_spotify_client():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope=SCOPE,
            cache_path=".spotify_cache"
        )
    )


def get_current_track(sp):
    data = sp.current_user_playing_track()

    if not data:
        return None

    if not data.get("is_playing"):
        return {
            "is_playing": False
        }

    item = data.get("item")

    if not item:
        return None

    track_name = item.get("name")
    artists = ", ".join([artist["name"] for artist in item.get("artists", [])])
    album_name = item.get("album", {}).get("name")
    duration_ms = item.get("duration_ms")
    progress_ms = data.get("progress_ms", 0)

    return {
        "is_playing": True,
        "track_name": track_name,
        "artists": artists,
        "album_name": album_name,
        "duration_ms": duration_ms,
        "progress_ms": progress_ms
    }


def main():
    sp = create_spotify_client()

    last_track = None
    current_lyrics = []
    last_lyric = ""

    while True:
        try:
            track = get_current_track(sp)

            if track is None:
                print("Không có bài nào đang phát.")
                current_lyrics = []
                last_lyric = ""

            elif not track["is_playing"]:
                print("Spotify đang pause.")
                last_lyric = ""

            else:
                current_track_key = f"{track['artists']} - {track['track_name']}"

                if current_track_key != last_track:
                    print("\n\n=== Bài mới ===")
                    print(f"Bài hát: {track['track_name']}")
                    print(f"Nghệ sĩ: {track['artists']}")
                    print(f"Album: {track['album_name']}")

                    duration_seconds = track["duration_ms"] // 1000

                    lrc = get_or_download_lrc(
                        track_name=track["track_name"],
                        artist_name=track["artists"],
                        album_name=track["album_name"],
                        duration_seconds=duration_seconds
                    )

                    if lrc:
                        current_lyrics = parse_lrc(lrc)
                        print(f"Đã load {len(current_lyrics)} dòng lyric.")
                    else:
                        current_lyrics = []
                        print("Bài này chưa có synced lyrics.")

                    last_track = current_track_key
                    last_lyric = ""

                current_time = ms_to_time(track["progress_ms"])
                duration_time = ms_to_time(track["duration_ms"])

                lyric = get_current_lyric(
                    lyrics=current_lyrics,
                    progress_ms=track["progress_ms"]
                )

                if lyric and lyric != last_lyric:
                    print()
                    print(f"[{current_time} / {duration_time}] {lyric}")
                    last_lyric = lyric
                else:
                    print(
                        f"Time: {current_time} / {duration_time}",
                        end="\r"
                    )

        except Exception as e:
            print("\nLỗi:", e)

        time.sleep(0.5)


if __name__ == "__main__":
    main()