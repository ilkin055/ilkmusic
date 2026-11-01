"""Mahnı axtarış tətbiqi: YouTube axtarışı, dinləmə, MP3 yükləmə və Shazam kimi tanıma."""

import array
import asyncio
import json
import logging
import math
import os
import re
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import wave
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from itertools import chain, zip_longest
from pathlib import Path

# FFmpeg sistem PATH-də deyil. Portativ versiyada tətbiqin yanındakı ffmpeg\ qovluğundadır,
# inkişaf kompüterində isə LOCALAPPDATA-dadır. Tapılanı yalnız bu prosesin PATH-inə əlavə edirik.
_FFMPEG_CANDIDATES = [
    os.environ.get("FFMPEG_DIR"),
    Path(__file__).resolve().parent.parent / "ffmpeg",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ffmpeg" / "bin",
]
FFMPEG_DIR = next((Path(c) for c in _FFMPEG_CANDIDATES if c and (Path(c) / "ffmpeg.exe").exists()), None)
if FFMPEG_DIR:
    os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")

# pydub (shazamio-nun asılılığı) ffmpeg-i import zamanı axtarır, ona görə bu importlar PATH-dən sonra gəlir.
import qrcode  # noqa: E402
import qrcode.image.svg  # noqa: E402
import yt_dlp  # noqa: E402
from fastapi import FastAPI, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.responses import FileResponse, PlainTextResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from shazamio import Shazam  # noqa: E402

FFMPEG = shutil.which("ffmpeg")
# print() əvəzinə: konsol cp1252 olanda "ə" kimi hərflər print()-i partladır, logging isə işi dayandırmır.
logger = logging.getLogger("uvicorn.error")
STATIC_DIR = Path(__file__).parent / "static"
CACHE_DIR = Path(tempfile.gettempdir()) / "ilkmusic-cache"
APP_ID = "ilkmusic"

SEARCH_LIMIT = 10
MAX_RECORDING_BYTES = 5 * 1024 * 1024

# F7: tarixçə hər kompüterdə ayrıca saxlanılır (ILKMUSIC_DATA_DIR testlərdə əsl tarixçəyə toxunmamaq üçündür).
DATA_DIR = Path(os.environ.get("ILKMUSIC_DATA_DIR") or Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "ilkmusic")
HISTORY_PATH = DATA_DIR / "history.json"
HISTORY_LIMIT = 50
RECENT_LIMIT = 12
SIMILAR_LIMIT = 16
SIMILAR_SEEDS = 3  # oxşar mahnılar son neçə mahnıya görə seçilir
RECOMMENDATION_CACHE_SECONDS = 30 * 60
POPULAR_QUERY = "Azərbaycan mahnıları yeni"  # tarixçə hələ boşdursa
# Eyni mahnının "Lyrics", "Official Video" kimi versiyalarını tanımaq üçün adlardan atılan sözlər.
TITLE_NOISE_WORDS = {
    "official", "video", "music", "audio", "lyrics", "lyric", "clip", "klip", "mv", "hd", "hq", "4k",
    "720p", "1080p", "full", "version", "new", "yeni", "by", "in", "the", "ft", "feat", "and", "ve", "və",
}

# Səhifə hər 20 saniyədən bir heartbeat göndərir. Bu müddətdə heç bir sorğu gəlməsə, səhifə bağlanıb deməkdir.
IDLE_TIMEOUT_SECONDS = 180
IDLE_CHECK_SECONDS = 30
# Telefon kilidlənəndə Safari heartbeat göndərmir: telefondan istifadə olunubsa, server daha uzun gözləyir.
PHONE_IDLE_TIMEOUT_SECONDS = 30 * 60

# Telefondan (ev Wi-Fi-ı ilə) giriş: kompüterin özündən gələn sorğular sərbəstdir, şəbəkədən gələnlər
# QR koddakı gizli açarı istəyir ki, eyni Wi-Fi-dakı başqası tətbiqdən istifadə edə bilməsin.
LOCAL_HOSTS = {"127.0.0.1", "::1"}
ACCESS_KEY_PATH = DATA_DIR / "access-key.txt"
ACCESS_COOKIE = "ilkmusic_key"
ACCESS_COOKIE_SECONDS = 365 * 24 * 3600
NO_ACCESS_MESSAGE = (
    "ilkmusic: icazə yoxdur.\n\n"
    "Kompüterdəki ilkmusic-də \"Telefonda aç\" düyməsinə bas və QR kodu telefonun kamerası ilə skan et."
)

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_URL_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
BAD_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

YDL_BASE_OPTS = {"quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True}

_download_locks: dict[str, threading.Lock] = {}
_download_locks_guard = threading.Lock()
_history_lock = threading.Lock()
_recommendation_cache: dict[str, tuple[float, list[dict]]] = {}

# run.py bunu təyin edir. uvicorn birbaşa işə salınanda (məs. inkişaf zamanı) None qalır və server özü dayanmır.
shutdown_hook: Callable[[], None] | None = None
_last_activity = time.monotonic()
_last_phone_activity: float | None = None


def _load_access_key() -> str:
    try:
        key = ACCESS_KEY_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        key = ""
    if not key:
        key = secrets.token_urlsafe(16)
        ACCESS_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        ACCESS_KEY_PATH.write_text(key, encoding="utf-8")
    return key


ACCESS_KEY = _load_access_key()


def _mark_activity() -> None:
    global _last_activity
    _last_activity = time.monotonic()


def _mark_phone_activity() -> None:
    global _last_phone_activity
    _last_phone_activity = time.monotonic()


async def _stop_when_idle() -> None:
    """Brauzerdə tətbiq səhifəsi qalmayanda serveri dayandırır."""
    while True:
        await asyncio.sleep(IDLE_CHECK_SECONDS)
        now = time.monotonic()
        phone_recent = _last_phone_activity is not None and now - _last_phone_activity < PHONE_IDLE_TIMEOUT_SECONDS
        if shutdown_hook and now - _last_activity > IDLE_TIMEOUT_SECONDS and not phone_recent:
            shutdown_hook()
            logger.info("Brauzerdə açıq səhifə qalmadı, tətbiq dayanır.")
            return


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Keş yalnız müvəqqətidir: MP3-lər istifadəçiyə brauzer vasitəsilə "Yükləmələr" qovluğuna verilir.
    shutil.rmtree(CACHE_DIR, ignore_errors=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if FFMPEG:
        logger.info("ffmpeg: %s", FFMPEG)
    else:
        logger.warning("ffmpeg tapılmadı. MP3 çevirmə və səslə axtarış işləməyəcək.")
    _mark_activity()
    idle_watcher = asyncio.create_task(_stop_when_idle())
    yield
    idle_watcher.cancel()
    shutil.rmtree(CACHE_DIR, ignore_errors=True)


app = FastAPI(title="ilkmusic", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _is_local(request: Request) -> bool:
    return request.client is not None and request.client.host in LOCAL_HOSTS


@app.middleware("http")
async def track_activity_and_revalidate_ui(request: Request, call_next):
    _mark_activity()
    local = _is_local(request)
    url_key = request.query_params.get("key")
    if not local:
        # Telefon: açar QR koddakı linklə gəlir (?key=...), sonra cookie-də saxlanılır.
        given = url_key or request.cookies.get(ACCESS_COOKIE) or ""
        if not secrets.compare_digest(given.encode(), ACCESS_KEY.encode()):
            return PlainTextResponse(NO_ACCESS_MESSAGE, status_code=403)
        _mark_phone_activity()
    response = await call_next(request)
    if not local and url_key:
        response.set_cookie(ACCESS_COOKIE, ACCESS_KEY, max_age=ACCESS_COOKIE_SECONDS, httponly=True, samesite="lax")
    # Kod yenilənəndə brauzer köhnə HTML/JS/CSS-i keşdən götürməsin.
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


def _lan_ip() -> str | None:
    """Kompüterin Wi-Fi/ev şəbəkəsindəki ünvanı (məs. 192.168.1.5)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            # UDP "connect" paket göndərmir, yalnız hansı şəbəkə kartının istifadə olunacağını müəyyən edir.
            sock.connect(("192.0.2.1", 80))
            return sock.getsockname()[0]
        except OSError:
            return None


def _ydl_error(exc: Exception) -> HTTPException:
    message = str(exc).removeprefix("ERROR: ").strip()
    return HTTPException(502, f"YouTube-dan cavab alınmadı: {message}")


def _video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _check_video_id(video_id: str) -> None:
    if not VIDEO_ID_RE.match(video_id):
        raise HTTPException(400, "Yanlış video ID.")


def _to_result(entry: dict) -> dict:
    video_id = entry["id"]
    return {
        "id": video_id,
        "title": entry.get("title") or video_id,
        "channel": entry.get("channel") or entry.get("uploader") or "",
        "duration": entry.get("duration"),
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
    }


def _safe_filename(title: str) -> str:
    name = BAD_FILENAME_CHARS_RE.sub("", title).strip(" .")
    return name[:150] or "mahni"


def _ensure_mp3(video_id: str) -> tuple[Path, dict]:
    """Mahnını YouTube-dan yükləyib MP3-ə çevirir (keşdə varsa, birbaşa qaytarır). Fayl və mahnı məlumatını qaytarır."""
    _check_video_id(video_id)
    mp3_path = CACHE_DIR / f"{video_id}.mp3"
    meta_path = CACHE_DIR / f"{video_id}.json"

    with _download_locks_guard:
        lock = _download_locks.setdefault(video_id, threading.Lock())

    with lock:
        if not mp3_path.exists():
            if not FFMPEG:
                raise HTTPException(500, "ffmpeg tapılmadı, MP3-ə çevirmək mümkün deyil.")
            opts = YDL_BASE_OPTS | {
                "format": "bestaudio/best",
                "outtmpl": str(CACHE_DIR / "%(id)s.%(ext)s"),
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ],
            }
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(_video_url(video_id), download=True)
            except yt_dlp.utils.DownloadError as exc:
                raise _ydl_error(exc) from exc
            if not mp3_path.exists():
                raise HTTPException(500, "MP3 faylı yaradılmadı.")
            meta_path.write_text(json.dumps(_to_result(info), ensure_ascii=False), encoding="utf-8")

    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return mp3_path, _to_result({"id": video_id} | meta)


def _cached(key: str, load: Callable[[], list[dict]]) -> list[dict]:
    """YouTube tövsiyələrini 30 dəqiqə yadda saxlayır ki, ana səhifə hər dəfə yavaş açılmasın."""
    hit = _recommendation_cache.get(key)
    if hit and time.monotonic() - hit[0] < RECOMMENDATION_CACHE_SECONDS:
        return hit[1]
    value = load()
    _recommendation_cache[key] = (time.monotonic(), value)
    return value


def _search_entries(query: str, limit: int) -> list[dict]:
    with yt_dlp.YoutubeDL(YDL_BASE_OPTS | {"extract_flat": "in_playlist"}) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    return [_to_result(e) for e in info.get("entries") or [] if VIDEO_ID_RE.match(e.get("id") or "")]


def _mix_entries(video_id: str) -> list[dict]:
    """YouTube Mix: YouTube-un bu mahnıya oxşar saydığı mahnılar."""
    opts = YDL_BASE_OPTS | {"extract_flat": "in_playlist", "noplaylist": False, "playlistend": 25}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"{_video_url(video_id)}&list=RD{video_id}", download=False)
    except yt_dlp.utils.DownloadError as exc:
        logger.warning("YouTube Mix alınmadı (%s): %s", video_id, exc)
        return []
    return [_to_result(e) for e in info.get("entries") or [] if VIDEO_ID_RE.match(e.get("id") or "")]


def _title_words(title: str) -> set[str]:
    # Yalnız latın hərfli sözlər (Azərbaycan hərfləri daxil): "Hasbi Rabbi | حسبي ربي" kimi
    # iki dildə yazılmış adlarda ərəbcə hissə müqayisəni pozmasın.
    words = re.findall(r"[a-zÀ-ɏə]+", title.lower())
    return {w for w in words if len(w) > 1 and w not in TITLE_NOISE_WORDS}


def _same_song(a: set[str], b: set[str]) -> bool:
    """"Sami Yusuf - Hasbi Rabbi (Lyrics)" və "Hasbi Rabbi (Sami Yusuf) HD" eyni mahnıdır, eyni ifaçının başqa mahnısı isə yox."""
    return bool(a and b) and len(a & b) / len(a | b) >= 0.5


def _load_history() -> list[dict]:
    try:
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return history if isinstance(history, list) else []


def _remember(track: dict) -> None:
    """Dinlənilən və ya yüklənən mahnını tarixçənin əvvəlinə qoyur."""
    with _history_lock:
        history = [t for t in _load_history() if t.get("id") != track["id"]]
        history.insert(0, track | {"played_at": int(time.time())})
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(json.dumps(history[:HISTORY_LIMIT], ensure_ascii=False, indent=1), encoding="utf-8")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/heartbeat")
def heartbeat():
    """Səhifə açıq olduqca çağırılır (aktivliyi middleware qeyd edir).

    run.py də bununla portdakı proqramın ilkmusic olub-olmadığını yoxlayır.
    """
    return {"app": APP_ID}


@app.get("/api/search")
def search(q: str):
    """F1: ad ilə axtarış, F2: YouTube linki ilə axtarış."""
    query = q.strip()
    if not query:
        raise HTTPException(400, "Axtarış sahəsi boşdur.")

    link = YOUTUBE_URL_RE.search(query)
    if not link and re.match(r"^https?://", query, re.IGNORECASE):
        raise HTTPException(400, "Hələlik yalnız YouTube linkləri dəstəklənir.")

    try:
        if link:
            with yt_dlp.YoutubeDL(YDL_BASE_OPTS) as ydl:
                entries = [ydl.extract_info(_video_url(link.group(1)), download=False)]
            results = [_to_result(e) for e in entries if VIDEO_ID_RE.match(e.get("id") or "")]
        else:
            results = _search_entries(query, SEARCH_LIMIT)
    except yt_dlp.utils.DownloadError as exc:
        raise _ydl_error(exc) from exc

    return {"type": "link" if link else "search", "results": results}


@app.get("/api/phone-link")
def phone_link(request: Request):
    """Telefonda açmaq üçün link və QR kod. Yalnız kompüterin özündən soruşmaq olar (açar içindədir)."""
    if not _is_local(request):
        raise HTTPException(403, "Bu link yalnız kompüterdə göstərilir.")
    ip = _lan_ip()
    if not ip or ip.startswith("127."):
        raise HTTPException(503, "Kompüter Wi-Fi və ya ev şəbəkəsinə qoşulmayıb.")
    url = f"http://{ip}:{request.url.port}/?key={ACCESS_KEY}"
    qr = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    return {"url": url, "svg": qr.to_string(encoding="unicode")}


@app.get("/api/history")
def history():
    """F7: "Son dinlədiklərin"."""
    return {"results": _load_history()[:RECENT_LIMIT]}


@app.delete("/api/history")
def clear_history():
    with _history_lock:
        HISTORY_PATH.unlink(missing_ok=True)
    return {"results": []}


@app.get("/api/similar")
def similar():
    """F7: "Sənə oxşar mahnılar" — son dinlənilən mahnıların YouTube Mix-lərindən, təkrarlar olmadan."""
    played = _load_history()
    if not played:
        try:
            return {"seeded": False, "results": _cached(f"search:{POPULAR_QUERY}", lambda: _search_entries(POPULAR_QUERY, SIMILAR_LIMIT))}
        except yt_dlp.utils.DownloadError as exc:
            raise _ydl_error(exc) from exc

    seeds = [t["id"] for t in played[:SIMILAR_SEEDS]]
    with ThreadPoolExecutor(max_workers=len(seeds)) as pool:
        mixes = list(pool.map(lambda video_id: _cached(f"mix:{video_id}", lambda: _mix_entries(video_id)), seeds))

    seen_ids = {t["id"] for t in played}
    seen_titles = [_title_words(t["title"]) for t in played[:10]]
    results = []
    # Hər mahnının Mix-indən növbə ilə götürürük ki, siyahı bir mahnıya bənzər mahnılarla dolmasın.
    for track in filter(None, chain.from_iterable(zip_longest(*mixes))):
        words = _title_words(track["title"])
        if track["id"] in seen_ids or any(_same_song(words, seen) for seen in seen_titles):
            continue
        seen_ids.add(track["id"])
        seen_titles.append(words)
        results.append(track)
        if len(results) >= SIMILAR_LIMIT:
            break
    return {"seeded": True, "results": results}


@app.post("/api/prepare/{video_id}")
def prepare(video_id: str):
    """Dinləmədən və ya yükləmədən əvvəl MP3-ü hazırlayır və mahnını tarixçəyə yazır."""
    _, track = _ensure_mp3(video_id)
    _remember(track)
    return track


@app.get("/api/audio/{video_id}")
def audio(video_id: str):
    """F5: tətbiqin içində dinləmək üçün."""
    mp3_path, _ = _ensure_mp3(video_id)
    return FileResponse(mp3_path, media_type="audio/mpeg")


@app.get("/api/download/{video_id}")
def download(video_id: str):
    """F4: MP3 faylını brauzerə "yüklə" kimi verir."""
    mp3_path, track = _ensure_mp3(video_id)
    return FileResponse(mp3_path, media_type="audio/mpeg", filename=f"{_safe_filename(track['title'])}.mp3")


def _level_db(wav_path: Path) -> float:
    """16-bit mono WAV-ın orta səs səviyyəsi (dBFS). -50 dB-dən aşağı demək olar ki, sükutdur."""
    with wave.open(str(wav_path)) as wav:
        samples = array.array("h", wav.readframes(wav.getnframes()))
    if not samples:
        return float("-inf")
    rms = math.sqrt(sum(s * s for s in samples) / len(samples))
    return 20 * math.log10(rms / 32768) if rms else float("-inf")


@app.post("/api/recognize")
async def recognize(audio: UploadFile):
    """F3: mikrofondan yazılmış səsi Shazam ilə tanıyır."""
    if not FFMPEG:
        raise HTTPException(500, "ffmpeg tapılmadı, səsi oxumaq mümkün deyil.")
    data = await audio.read()
    if not data:
        raise HTTPException(400, "Səs yazısı boşdur.")
    if len(data) > MAX_RECORDING_BYTES:
        raise HTTPException(413, "Səs yazısı çox böyükdür.")

    with tempfile.TemporaryDirectory(prefix="mahni-rec-") as tmp:
        src_path = Path(tmp) / "recording"
        wav_path = Path(tmp) / "recording.wav"
        src_path.write_bytes(data)
        # Brauzer adətən webm/opus göndərir. Shazam üçün onu mono WAV-a çeviririk.
        proc = await asyncio.to_thread(
            subprocess.run,
            [FFMPEG, "-y", "-loglevel", "error", "-i", str(src_path), "-ac", "1", "-ar", "16000", str(wav_path)],
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0 or not wav_path.exists():
            raise HTTPException(400, "Səs yazısını oxumaq mümkün olmadı.")
        level_db = _level_db(wav_path)
        try:
            result = await Shazam().recognize(str(wav_path))
        except Exception as exc:
            raise HTTPException(502, f"Shazam-a qoşulmaq alınmadı: {exc}") from exc

    track = result.get("track")
    # Səslə axtarış tapmayanda səbəbi görmək üçün: səviyyə çox aşağıdırsa, mikrofon mahnını eşitməyib.
    logger.info(
        "Səslə axtarış: %d KB, səviyyə %.1f dB, nəticə: %s",
        len(data) // 1024,
        level_db,
        f"{track.get('subtitle', '')} - {track.get('title', '')}" if track else "tanınmadı",
    )
    if not track:
        return {"found": False}
    return {
        "found": True,
        "title": track.get("title", ""),
        "artist": track.get("subtitle", ""),
        "cover": (track.get("images") or {}).get("coverart"),
    }
