import os
import json
import shutil
import requests
from datetime import datetime
from urllib.parse import urlencode
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

app = FastAPI()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "1c7e4468652645468c635ad74808d8f0")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "b9f88cc5f25f44059de3799dd172cee4")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/callback")
HF_TOKEN = os.getenv("HF_TOKEN", "")

TOKEN_FILE = "spotify_token.json"
os.makedirs("memories", exist_ok=True)
app.mount("/memories", StaticFiles(directory="memories"), name="memories")

# Instant lookup so pins never stack on one spot when offline
KNOWN_COORDS = {
    "kazakhstan": (48.0196, 66.9237),
    "almaty": (43.2220, 76.8512),
    "astana": (51.1694, 71.4491),
    "germany": (51.1657, 10.4515),
    "berlin": (52.5200, 13.4050),
    "munich": (48.1351, 11.5820),
    "united states": (37.0902, -95.7129),
    "usa": (37.0902, -95.7129),
    "new york": (40.7128, -74.0060),
    "california": (36.7783, -119.4179),
    "japan": (36.2048, 138.2529),
    "tokyo": (35.6762, 139.6503),
    "france": (46.2276, 2.2137),
    "paris": (48.8566, 2.3522),
    "uk": (55.3781, -3.4360),
    "london": (51.5072, -0.1276),
    "italy": (41.8719, 12.5674),
    "rome": (41.9028, 12.4964),
    "austria": (47.5162, 14.5501),
    "vienna": (48.2082, 16.3738),
    "switzerland": (46.8182, 8.2275),
    "turkey": (38.9637, 35.2433),
    "istanbul": (41.0082, 28.9784),
    "south korea": (35.9078, 127.7669),
    "seoul": (37.5665, 126.9780),
    "canada": (56.1304, -106.3468),
    "brazil": (-14.2350, -51.9253),
    "australia": (-25.2744, 133.7751),
    "uae": (23.4241, 53.8478),
    "dubai": (25.2048, 55.2708),
    "spain": (40.4637, -3.7492),
    "china": (35.8617, 104.1954),
}

def resolve_coordinates(location_str: str):
    loc_lower = (location_str or "").strip().lower()
    for key, (lat, lon) in KNOWN_COORDS.items():
        if key in loc_lower:
            return lat, lon
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location_str, "format": "json", "limit": 1},
            headers={"User-Agent": "AtmosphereDiaryArtTech/1.0"},
            timeout=3
        )
        if r.status_code == 200 and r.json():
            item = r.json()[0]
            return float(item["lat"]), float(item["lon"])
    except Exception:
        pass
    # Deterministic hash fallback so different unknown places never overlap
    h = sum(ord(c) * (i + 1) for i, c in enumerate(loc_lower or "default"))
    lat = ((h % 110) - 45) + 0.25
    lon = (((h * 7) % 320) - 160) + 0.25
    return float(lat), float(lon)

def save_tokens(data):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def get_client_token():
    try:
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID.strip(), SPOTIFY_CLIENT_SECRET.strip()),
            timeout=6,
        )
        if res.status_code == 200:
            return res.json().get("access_token")
    except Exception:
        pass
    return None

def get_user_session():
    tokens = load_tokens()
    tok = tokens.get("access_token")
    if not tok:
        return None, None, "not_logged_in"

    me_res = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": f"Bearer {tok}"}, timeout=5)
    if me_res.status_code == 200:
        return tok, me_res.json(), None
    if me_res.status_code == 403:
        return tok, None, "403_user_not_added_in_dashboard"

    ref = tokens.get("refresh_token")
    if ref:
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "refresh_token", "refresh_token": ref},
            auth=(SPOTIFY_CLIENT_ID.strip(), SPOTIFY_CLIENT_SECRET.strip()),
            timeout=5
        )
        if r.status_code == 200:
            new_d = r.json()
            new_d.setdefault("refresh_token", ref)
            save_tokens(new_d)
            new_tok = new_d.get("access_token")
            me_retry = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": f"Bearer {new_tok}"}, timeout=5)
            if me_retry.status_code == 200:
                return new_tok, me_retry.json(), None

    return None, None, "token_expired"

def extract_spotify_tracks(items):
    tracks = []
    for item in items:
        if not isinstance(item, dict):
            continue
        t = item.get("track", item) if "track" in item else item
        if not isinstance(t, dict):
            continue
        url = t.get("external_urls", {}).get("spotify")
        if url:
            artists = ", ".join(a.get("name", "") for a in t.get("artists", []) if a.get("name"))
            images = t.get("album", {}).get("images", [])
            cover = images[0].get("url") if images else ""
            tracks.append({
                "title": t.get("name", "Track"),
                "artist": artists,
                "name": f"{t.get('name', 'Track')} — {artists}",
                "url": url,
                "preview_url": t.get("preview_url") or "",
                "cover": cover
            })
    return tracks

def fallback_music_search(query: str):
    tracks = []
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "entity": "song", "limit": 25},
            timeout=6
        )
        if r.status_code == 200:
            for item in r.json().get("results", []):
                title = item.get("trackName", "Track")
                artist = item.get("artistName", "Artist")
                preview = item.get("previewUrl", "")
                cover = (item.get("artworkUrl100") or "").replace("100x100bb", "300x300bb")
                if preview:
                    tracks.append({
                        "title": title,
                        "artist": artist,
                        "name": f"{title} — {artist}",
                        "url": preview,
                        "preview_url": preview,
                        "cover": cover
                    })
    except Exception:
        pass
    return tracks

@app.get("/")
def serve_ui():
    return FileResponse("index.html")

@app.get("/api/spotify/login")
def spotify_login():
    params = {
        "client_id": SPOTIFY_CLIENT_ID.strip(),
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": "user-read-private user-read-email user-library-read playlist-read-private playlist-read-collaborative user-top-read user-read-recently-played",
        "show_dialog": "true"
    }
    return RedirectResponse("https://accounts.spotify.com/authorize?" + urlencode(params))

@app.get("/callback")
def spotify_callback(code: str = "", error: str = ""):
    if error or not code:
        return RedirectResponse(f"/?spotify_error={error or 'no_code'}")
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
        },
        auth=(SPOTIFY_CLIENT_ID.strip(), SPOTIFY_CLIENT_SECRET.strip())
    )
    if res.status_code == 200:
        save_tokens(res.json())
        return RedirectResponse("/?spotify=connected")
    return RedirectResponse("/?spotify_error=token_failed")

@app.get("/api/spotify/playlists")
def get_user_playlists():
    user_token, profile, _ = get_user_session()
    curated = [
        {"id": "vibe:dreamy ambient", "name": "☁️ Dreamy & Ambient Vibes"},
        {"id": "vibe:late night chill", "name": "🌙 Late Night Chill"},
        {"id": "vibe:indie nostalgia", "name": "🎞️ Indie Nostalgia"},
        {"id": "vibe:underground rap", "name": "🔥 Underground & Cloud Rap"}
    ]

    if not user_token or not profile:
        return {"connected": False, "playlists": curated}

    headers = {"Authorization": f"Bearer {user_token}"}
    user_id = profile.get("id", "")
    display_name = profile.get("display_name") or user_id

    user_lists = [
        {"id": "liked", "name": f"❤️ {display_name}'s Liked Songs"},
        {"id": "top", "name": f"✨ {display_name}'s Top & Recent"}
    ]

    res = requests.get("https://api.spotify.com/v1/me/playlists?limit=50", headers=headers)
    items = res.json().get("items", []) if res.status_code == 200 else []
    if not items and user_id:
        res2 = requests.get(f"https://api.spotify.com/v1/users/{user_id}/playlists?limit=50", headers=headers)
        if res2.status_code == 200:
            items = res2.json().get("items", [])

    for item in items:
        if item and item.get("id"):
            total = item.get("tracks", {}).get("total", 0)
            user_lists.append({
                "id": item["id"],
                "name": f"🎵 {item.get('name', 'Playlist')} ({total})"
            })

    return {"connected": True, "user": display_name, "playlists": user_lists + curated}

@app.get("/api/spotify/playlist-tracks/{playlist_id}")
def get_playlist_tracks(playlist_id: str):
    user_token, _, _ = get_user_session()
    tracks = []

    if playlist_id.startswith("vibe:"):
        query = playlist_id.split("vibe:", 1)[1]
        tracks = fallback_music_search(query) or fallback_music_search("chill lofi")
        return {"tracks": tracks, "source": "curated"}

    if user_token:
        headers = {"Authorization": f"Bearer {user_token}"}
        if playlist_id == "liked":
            res = requests.get("https://api.spotify.com/v1/me/tracks?market=from_token&limit=50", headers=headers)
            if res.status_code == 200:
                tracks = extract_spotify_tracks(res.json().get("items", []))
        elif playlist_id == "top":
            res = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=40", headers=headers)
            if res.status_code == 200:
                tracks = extract_spotify_tracks(res.json().get("items", []))
            if not tracks:
                res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=40", headers=headers)
                if res.status_code == 200:
                    tracks = extract_spotify_tracks(res.json().get("items", []))
        else:
            res = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?market=from_token&limit=50", headers=headers)
            if res.status_code == 200:
                tracks = extract_spotify_tracks(res.json().get("items", []))

    return {"tracks": tracks, "source": "user"}

@app.get("/api/spotify/search")
def search_spotify_tracks(q: str):
    if not q.strip():
        return {"tracks": []}
    tracks = fallback_music_search(q.strip())
    if not tracks:
        tok, _, _ = get_user_session()
        tok = tok or get_client_token()
        if tok:
            res = requests.get(
                "https://api.spotify.com/v1/search",
                params={"q": q.strip(), "type": "track", "market": "US", "limit": 25},
                headers={"Authorization": f"Bearer {tok}"}
            )
            if res.status_code == 200:
                tracks = extract_spotify_tracks(res.json().get("tracks", {}).get("items", []))
    return {"tracks": tracks}

@app.get("/api/archive")
def get_archive():
    entries = []
    for folder in sorted(os.listdir("memories")):
        meta_path = os.path.join("memories", folder, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Backfill missing date or fix duplicate default coordinates on existing memories
                    if not data.get("date"):
                        data["date"] = datetime.now().strftime("%Y-%m-%d")
                    lat, lon = resolve_coordinates(data.get("location", "Germany"))
                    if data.get("lat") in (None, 51.16) and "germany" not in (data.get("location", "").lower()):
                        data["lat"], data["lon"] = lat, lon
                    entries.append(data)
            except Exception:
                pass
    return entries

@app.post("/api/create-memory")
async def create_memory(
    text: str = Form(...),
    location: str = Form("Almaty, Kazakhstan"),
    memory_date: str = Form(""),
    importance: int = Form(3),
    song_url: str = Form(""),
    song_title: str = Form(""),
    song_artist: str = Form(""),
    song_cover: str = Form(""),
    photo: UploadFile = File(None),       # Optional
    glb_file: UploadFile = File(None)     # Optional
):
    lat, lon = resolve_coordinates(location)
    final_date = memory_date.strip() if memory_date.strip() else datetime.now().strftime("%Y-%m-%d")

    # AI title/color generation fallback...
    base_title = "Memory"
    safe_title = f"{base_title}_{datetime.now().strftime('%H%M%S')}"
    folder_path = os.path.join("memories", safe_title)
    os.makedirs(folder_path, exist_ok=True)

    # Fallback image if no photo is uploaded
    if photo and photo.filename:
        photo_filename = f"photo_{photo.filename}"
        photo_path = os.path.join(folder_path, photo_filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/memories/{safe_title}/{photo_filename}"
    else:
        photo_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1000&q=80"

    glb_url = ""
    splat_url = ""

    if glb_file and glb_file.filename:
        ext = os.path.splitext(glb_file.filename)[1].lower()
        model_filename = f"model_{glb_file.filename}"
        model_path = os.path.join(folder_path, model_filename)
        with open(model_path, "wb") as buffer:
            shutil.copyfileobj(glb_file.file, buffer)
        if ext in [".ply", ".splat", ".ksplat"]:
            splat_url = f"/memories/{safe_title}/{model_filename}"
        else:
            glb_url = f"/memories/{safe_title}/{model_filename}"

    metadata = {
        "id": safe_title,
        "title": base_title,
        "date": final_date,
        "text": text,
        "location": location,
        "importance": int(importance),
        "lat": lat,
        "lon": lon,
        "song_url": song_url,
        "song_title": song_title,
        "song_artist": song_artist,
        "song_cover": song_cover,
        "photo_url": photo_url,
        "glb_url": glb_url,
        "splat_url": splat_url
    }
    with open(os.path.join(folder_path, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata