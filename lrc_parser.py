import re
from dataclasses import dataclass


@dataclass
class LyricLine:
    time_ms: int
    text: str


def parse_timestamp(timestamp: str) -> int:
    """
    Chuyển timestamp dạng:
    00:12.50
    00:12.500

    sang milliseconds.
    """
    minutes, seconds = timestamp.split(":")
    seconds, milliseconds = seconds.split(".")

    total_ms = (
        int(minutes) * 60 * 1000
        + int(seconds) * 1000
        + int(milliseconds.ljust(3, "0")[:3])
    )

    return total_ms


def parse_lrc(lrc_text: str):
    """
    Parse nội dung .lrc thành list LyricLine.
    Ví dụ:
    [00:12.50]Hello world
    """
    lines = []

    pattern = r"\[(\d{2}:\d{2}\.\d{2,3})\](.*)"

    for raw_line in lrc_text.splitlines():
        match = re.match(pattern, raw_line)

        if not match:
            continue

        timestamp = match.group(1)
        text = match.group(2).strip()

        if not text:
            continue

        lines.append(
            LyricLine(
                time_ms=parse_timestamp(timestamp),
                text=text
            )
        )

    lines.sort(key=lambda x: x.time_ms)
    return lines


def get_current_lyric(lyrics, progress_ms: int):
    """
    Lấy dòng lyric hiện tại.
    """
    if not lyrics:
        return ""

    current = ""

    for line in lyrics:
        if line.time_ms <= progress_ms:
            current = line.text
        else:
            break

    return current


def get_lyric_context(lyrics, progress_ms: int):
    """
    Trả về 3 dòng:
    - previous lyric
    - current lyric
    - next lyric
    """
    if not lyrics:
        return "", "", ""

    current_index = 0

    for i, line in enumerate(lyrics):
        if line.time_ms <= progress_ms:
            current_index = i
        else:
            break

    previous_text = lyrics[current_index - 1].text if current_index - 1 >= 0 else ""
    current_text = lyrics[current_index].text if current_index < len(lyrics) else ""
    next_text = lyrics[current_index + 1].text if current_index + 1 < len(lyrics) else ""

    return previous_text, current_text, next_text