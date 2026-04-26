import sys
import os

from dotenv import load_dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from lyrics_client import get_or_download_lrc
from lrc_parser import parse_lrc, get_lyric_context
from overlay_ui import LyricsOverlay

LYRIC_OFFSET_MS = 100

load_dotenv()

SCOPE = "user-read-currently-playing"


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
    """
    Lấy bài đang phát hiện tại từ Spotify.
    """
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

    artists = ", ".join(
        [artist["name"] for artist in item.get("artists", [])]
    )

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


class SpotifyLyricsApp:
    def __init__(self):
        self.sp = create_spotify_client()

        self.overlay = LyricsOverlay()
        self.overlay.show()

        self.last_track_key = None
        self.current_lyrics = [] 
        self.last_current_lyric = ""

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(500)

    def update(self):
        try:
            track = get_current_track(self.sp)

            if track is None:
                self.overlay.set_lyric("Không có bài nào đang phát")
                self.current_lyrics = []
                self.last_track_key = None
                self.last_current_lyric = ""
                return

            if not track["is_playing"]:
                self.overlay.set_lyric("Spotify đang pause")
                self.last_current_lyric = ""
                return

            current_track_key = f"{track['artists']} - {track['track_name']}"

            if current_track_key != self.last_track_key:
                self.load_new_track(track)
                self.last_track_key = current_track_key

            previous_lyric, current_lyric, next_lyric = get_lyric_context(
                lyrics=self.current_lyrics,
                progress_ms=track["progress_ms"] + LYRIC_OFFSET_MS
            )

            if current_lyric:
                if current_lyric != self.last_current_lyric:
                    self.overlay.set_lyric_context(
                        previous_text=previous_lyric,
                        current_text=current_lyric,
                        next_text=next_lyric
                    )
                    self.last_current_lyric = current_lyric
            else:
                self.overlay.set_lyric(
                    f"{track['track_name']} - {track['artists']}"
                )

            # Ép overlay nổi lại sau mỗi lần update
            if hasattr(self.overlay, "force_topmost"):
                self.overlay.force_topmost() 

        except Exception as e:
            self.overlay.set_lyric(f"Lỗi: {e}")

    def load_new_track(self, track):
        self.overlay.set_lyric(
            f"Đang tải lyrics: {track['track_name']}"
        )

        duration_seconds = track["duration_ms"] // 1000

        lrc = get_or_download_lrc(
            track_name=track["track_name"],
            artist_name=track["artists"],
            album_name=track["album_name"],
            duration_seconds=duration_seconds 
        )

        if lrc:
            self.current_lyrics = parse_lrc(lrc)
            self.last_current_lyric = ""

            self.overlay.set_lyric(
                f"Đã tải lyrics: {len(self.current_lyrics)} dòng"
            )
        else:
            self.current_lyrics = []
            self.last_current_lyric = ""

            self.overlay.set_lyric(
                f"Không có synced lyrics: {track['track_name']}"
            )


def main():
    app = QApplication(sys.argv)

    spotify_lyrics_app = SpotifyLyricsApp()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()