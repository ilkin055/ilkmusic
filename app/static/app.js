const form = document.getElementById("search-form");
const input = document.getElementById("q");
const micBtn = document.getElementById("mic");
const statusEl = document.getElementById("status");
const homeView = document.getElementById("home-view");
const searchView = document.getElementById("search-view");
const recentShelf = document.getElementById("recent-shelf");
const recentEl = document.getElementById("recent");
const similarEl = document.getElementById("similar");
const similarTitle = document.getElementById("similar-title");
const resultsEl = document.getElementById("results");
const searchTitle = document.getElementById("search-title");
const player = document.getElementById("player");
const audio = document.getElementById("audio");
const nowPlaying = document.getElementById("now-playing");
const nowCover = document.getElementById("now-cover");

const RECORD_SECONDS = 10;
const SKELETON_CARDS = 8;

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

async function api(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch {
    throw new Error("Serverə qoşulmaq olmur. Tətbiq bağlanıb: ilkmusic ikonuna yenidən bas.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Xəta: ${res.status}`);
  return data;
}

function formatDuration(totalSeconds) {
  if (!totalSeconds) return "";
  const sec = Math.round(totalSeconds);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = String(sec % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

function makeButton(label, onClick) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = label;
  btn.addEventListener("click", () => onClick(btn));
  return btn;
}

// Düymə və kartın şəkli MP3 hazırlanarkən "Hazırlanır…" göstərir.
async function withBusy(btn, fn) {
  const label = btn.textContent;
  const card = btn.closest(".card");
  const icon = card?.querySelector(".play-icon");
  btn.disabled = true;
  btn.textContent = "Hazırlanır…";
  card?.classList.add("busy");
  if (icon) icon.textContent = "Hazırlanır…";
  try {
    await fn();
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = label;
    card?.classList.remove("busy");
    if (icon) icon.textContent = "▶";
  }
}

// F5: tətbiqin içində dinləmək
function playTrack(track, btn) {
  return withBusy(btn, async () => {
    const info = await api(`/api/prepare/${track.id}`, { method: "POST" });
    nowPlaying.textContent = info.title || track.title;
    nowCover.src = track.thumbnail;
    player.hidden = false;
    audio.src = `/api/audio/${track.id}`;
    await audio.play();
    afterListen();
  });
}

// F4: MP3 yükləmə (brauzer faylı "Yükləmələr" qovluğuna salır)
function downloadTrack(track, btn) {
  return withBusy(btn, async () => {
    await api(`/api/prepare/${track.id}`, { method: "POST" });
    const link = document.createElement("a");
    link.href = `/api/download/${track.id}`;
    link.download = "";
    document.body.append(link);
    link.click();
    link.remove();
    afterListen();
  });
}

// YouTube kimi kart: şəkil (üstünə basanda çalır), ad, kanal, düymələr.
function makeCard(track) {
  const card = document.createElement("article");
  card.className = "card";

  const thumb = document.createElement("button");
  thumb.type = "button";
  thumb.className = "thumb";
  thumb.title = "Dinlə";
  const img = document.createElement("img");
  img.src = track.thumbnail;
  img.alt = "";
  img.loading = "lazy";
  const playIcon = document.createElement("span");
  playIcon.className = "play-icon";
  playIcon.textContent = "▶";
  thumb.append(img, playIcon);
  const duration = formatDuration(track.duration);
  if (duration) {
    const badge = document.createElement("span");
    badge.className = "duration";
    badge.textContent = duration;
    thumb.append(badge);
  }

  const body = document.createElement("div");
  body.className = "card-body";
  const title = document.createElement("div");
  title.className = "title";
  title.textContent = track.title;
  title.title = track.title;
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = track.channel || "";

  const actions = document.createElement("div");
  actions.className = "card-actions";
  const playBtn = makeButton("▶ Dinlə", (btn) => playTrack(track, btn));
  actions.append(playBtn, makeButton("⬇ MP3", (btn) => downloadTrack(track, btn)));
  thumb.addEventListener("click", () => playBtn.click());

  body.append(title, meta, actions);
  card.append(thumb, body);
  return card;
}

function renderGrid(container, tracks, emptyText = "") {
  container.replaceChildren(...tracks.map(makeCard));
  if (!tracks.length && emptyText) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = emptyText;
    container.append(empty);
  }
}

function renderSkeleton(container) {
  const cards = Array.from({ length: SKELETON_CARDS }, () => {
    const card = document.createElement("div");
    card.className = "card skeleton";
    card.innerHTML = '<div class="thumb"></div><div class="line"></div><div class="line short"></div>';
    return card;
  });
  container.replaceChildren(...cards);
}

// F7: ana səhifə — "Son dinlədiklərin" və "Sənə oxşar mahnılar"
let similarStale = true;
let similarRequest = 0;

async function loadRecent() {
  try {
    const data = await api("/api/history");
    recentShelf.hidden = !data.results.length;
    renderGrid(recentEl, data.results);
  } catch {
    recentShelf.hidden = true;
  }
}

async function loadSimilar() {
  similarStale = false;
  const request = ++similarRequest;
  renderSkeleton(similarEl);
  try {
    const data = await api("/api/similar");
    if (request !== similarRequest) return; // arada daha yeni sorğu göndərilib
    similarTitle.textContent = data.seeded ? "Sənə oxşar mahnılar" : "Populyar mahnılar";
    renderGrid(similarEl, data.results, "Hələlik tövsiyə yoxdur.");
  } catch (err) {
    if (request !== similarRequest) return;
    renderGrid(similarEl, [], err.message);
    similarStale = true;
  }
}

// Yeni mahnı dinlənəndə "Son dinlədiklərin" dərhal yenilənir, tövsiyələr isə ana səhifəyə qayıdanda.
function afterListen() {
  loadRecent();
  similarStale = true;
}

function showHome() {
  searchView.hidden = true;
  homeView.hidden = false;
  setStatus("");
  if (similarStale) loadSimilar();
}

function showSearch() {
  homeView.hidden = true;
  searchView.hidden = false;
}

// F1 və F2: ad və ya YouTube linki ilə axtarış. Uğurlu olsa, status mətnini qaytarır.
async function search(query) {
  const q = query.trim();
  if (!q) return null;
  showSearch();
  searchTitle.textContent = `"${q}" üçün nəticələr`;
  setStatus("Axtarılır…");
  renderSkeleton(resultsEl);
  try {
    const data = await api(`/api/search?q=${encodeURIComponent(q)}`);
    if (data.type === "link") searchTitle.textContent = "Linkdəki mahnı";
    renderGrid(resultsEl, data.results, "Heç nə tapılmadı.");
    let text = "Heç nə tapılmadı.";
    if (data.results.length) {
      text = data.type === "link" ? "Linkdəki mahnı tapıldı." : `${data.results.length} nəticə tapıldı.`;
    }
    setStatus(text);
    return text;
  } catch (err) {
    resultsEl.replaceChildren();
    setStatus(err.message, true);
    return null;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  search(input.value);
});

document.getElementById("home-link").addEventListener("click", (event) => {
  event.preventDefault();
  input.value = "";
  showHome();
});

document.getElementById("back-home").addEventListener("click", () => showHome());

document.getElementById("clear-history").addEventListener("click", async () => {
  if (!confirm("Son dinlədiklərin siyahısı silinsin?")) return;
  try {
    await api("/api/history", { method: "DELETE" });
    await loadRecent();
    loadSimilar();
  } catch (err) {
    setStatus(err.message, true);
  }
});

// F3: Shazam kimi səslə axtarış
// Brauzerin standart səs emalı (əks-səda və küy silmə) danışıq üçündür: musiqini korlayır,
// kompüterin öz dinamiklərindən çalınan mahnını isə "əks-səda" sayıb tamamilə silir.
const MIC_CONSTRAINTS = { audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } };
const QUIET_LEVEL = 0.02; // RMS: bundan aşağı olsa, mikrofon demək olar ki, heç nə eşitməyib
const LEVEL_BARS = 8;

function levelBar(level) {
  const filled = Math.min(LEVEL_BARS, Math.round(level * 40));
  return "▮".repeat(filled) + "▯".repeat(LEVEL_BARS - filled);
}

// Axından RECORD_SECONDS saniyə yazır, səs səviyyəsini göstərir və Shazam-a göndərir.
async function recognizeFromStream(stream) {
  const audioCtx = new AudioContext();
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048;
  audioCtx.createMediaStreamSource(stream).connect(analyser);
  const samples = new Float32Array(analyser.fftSize);
  let loudest = 0;
  const readLevel = () => {
    analyser.getFloatTimeDomainData(samples);
    let sum = 0;
    for (const s of samples) sum += s * s;
    const rms = Math.sqrt(sum / samples.length);
    loudest = Math.max(loudest, rms);
    return rms;
  };

  const recorder = new MediaRecorder(stream);
  const chunks = [];
  recorder.ondataavailable = (event) => {
    if (event.data.size) chunks.push(event.data);
  };
  const stopped = new Promise((resolve) => {
    recorder.onstop = resolve;
  });

  recorder.start();
  const endAt = Date.now() + RECORD_SECONDS * 1000;
  while (Date.now() < endAt) {
    const left = Math.ceil((endAt - Date.now()) / 1000);
    setStatus(`🎤 Dinləyirəm… ${left} san   Səs: ${levelBar(readLevel())}`);
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  recorder.stop();
  await stopped;
  audioCtx.close();

  setStatus("Mahnı tanınır…");
  const body = new FormData();
  body.append("audio", new Blob(chunks, { type: recorder.mimeType }), "recording");
  const data = await api("/api/recognize", { method: "POST", body });
  if (!data.found) {
    setStatus(
      loudest < QUIET_LEVEL
        ? "Mikrofon demək olar ki, heç nə eşitmədi. Mahnını daha ucadan çal və ya telefonu mikrofona yaxınlaşdır."
        : "Mahnı tanınmadı. Nəqarət hissəsini çalıb yenidən cəhd et. Çox yerli mahnılar Shazam bazasında olmaya bilər.",
      true,
    );
    return;
  }

  const q = `${data.artist} ${data.title}`.trim();
  input.value = q;
  const searchStatus = await search(q);
  if (searchStatus) setStatus(`Tanındı: ${data.artist} — ${data.title}. ${searchStatus}`);
}

async function recordAndRecognize() {
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia(MIC_CONSTRAINTS);
  } catch {
    setStatus(
      "Mikrofona icazə verilmədi və ya mikrofon tapılmadı. Ünvan sətrinin solundakı ikona basıb mikrofona icazə ver.",
      true,
    );
    return;
  }

  micBtn.disabled = true;
  try {
    await recognizeFromStream(stream);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    stream.getTracks().forEach((t) => t.stop());
    micBtn.disabled = false;
  }
}

micBtn.addEventListener("click", recordAndRecognize);

// Tətbiq pəncərəsiz işləyir: səhifə açıq olduqca serverə xəbər veririk, bağlananda server özü dayanır.
const HEARTBEAT_MS = 20000;
function heartbeat() {
  fetch("/api/heartbeat", { method: "POST" }).catch(() => {});
}
heartbeat();
setInterval(heartbeat, HEARTBEAT_MS);

loadRecent();
loadSimilar();
