# Spotify Lyrics Overlay

Ứng dụng hiển thị lyrics đang phát trên Spotify bằng Python.

## Tính năng

- Lấy bài đang phát từ Spotify API
- Tìm synced lyrics từ LRCLIB
- Hiển thị lyrics bằng overlay PySide6
- Cache lyrics local

## Cài đặt

```bash
pip install -r requirements.txt
```

## Config API

1. Tạo app trên Spotify Developer Dashboard
2. Lấy Client ID & Client Secret
3. Cập nhật vào file `.env`:

   ```env
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   ```

## Cách dùng

```bash
python3 main.py
```

## Lưu ý

- Cần Spotify đang mở và phát nhạc
- Cần quyền truy cập vào Spotify API