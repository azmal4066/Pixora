import json, pathlib, re, shutil, subprocess, tempfile, os
import numpy as np
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="PIXORA – Creative Studio", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")
ROOT = pathlib.Path(__file__).parent / "pixora"
st.markdown("<style>header,footer{visibility:hidden}.block-container{padding:0.5rem 1rem}</style>", unsafe_allow_html=True)


@st.cache_data
def studio_html() -> str:
    """Inline the local CSS/JS so the whole studio runs inside one component."""
    h = (ROOT / "index.html").read_text(encoding="utf-8")
    h = re.sub(r'<link rel="stylesheet" href="(css/[^"]+)">',
               lambda m: "<style>" + (ROOT / m.group(1)).read_text(encoding="utf-8") + "</style>", h)
    h = re.sub(r'<script src="(js/[^"]+)"></script>',
               lambda m: "<script>" + (ROOT / m.group(1)).read_text(encoding="utf-8").replace("</script>", "<\\/script>") + "</script>", h)
    return h


@st.cache_resource(show_spinner="Loading Whisper model…")
def load_model(size: str):
    from faster_whisper import WhisperModel
    return WhisperModel(size, device="cpu", compute_type="int8")


def decode_audio_ffmpeg(path: str, sr: int = 16000) -> np.ndarray:
    """Decode any audio/video file to mono float32 @16 kHz using ffmpeg.
    Bypasses PyAV (av.open), which crashes with a TypeError on newer Python/PyAV builds."""
    exe = shutil.which("ffmpeg")
    if not exe:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, "-nostdin", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError("ffmpeg could not decode this file: " + p.stderr.decode(errors="ignore")[:300])
    return np.frombuffer(p.stdout, dtype=np.float32)


SP_RE = re.compile(r"open\.spotify\.com/(?:intl-[a-z-]+/)?(?:embed/)?(track|album|playlist|episode|show|artist)/([A-Za-z0-9]+)|spotify:(track|album|playlist|episode|show|artist):([A-Za-z0-9]+)", re.I)


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _sp_creds():
    """Spotify Client ID/Secret live in Streamlit secrets (never in browser code)."""
    try:
        return st.secrets["SPOTIFY_CLIENT_ID"], st.secrets["SPOTIFY_CLIENT_SECRET"]
    except Exception:
        return os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET")


@st.cache_data(ttl=3000, show_spinner=False)
def _sp_token(cid: str, secret: str) -> str:
    r = requests.post("https://accounts.spotify.com/api/token", data={"grant_type": "client_credentials"},
                      auth=(cid, secret), timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


@st.cache_data(ttl=300, show_spinner=False)
def sp_search(q: str, offset: int, cid: str, secret: str) -> list:
    # Spotify caps search at 10 results per request (Feb 2026) -> paginate with offset.
    r = requests.get("https://api.spotify.com/v1/search", headers={"Authorization": f"Bearer {_sp_token(cid, secret)}"},
                     params={"q": q, "type": "track", "limit": 10, "offset": offset}, timeout=15)
    r.raise_for_status()
    return r.json()["tracks"]["items"]


def sp_embed(link: str):
    m = SP_RE.search(link or "")
    if not m:
        return False
    kind, sid = (m.group(1) or m.group(3)).lower(), m.group(2) or m.group(4)
    h = 152 if kind in ("track", "episode") else 352
    components.html(f'<iframe src="https://open.spotify.com/embed/{kind}/{sid}?utm_source=generator" width="100%" height="{h}" '
                    f'frameborder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" '
                    f'loading="lazy" style="border-radius:12px"></iframe>', height=h + 8)
    return True


def spotify_panel(key: str):
    """Search Spotify in-app (needs secrets), or paste a link; then play it."""
    cid, secret = _sp_creds()
    link = ""
    if cid and secret:
        q = st.text_input("🔍 Search songs on Spotify", key=f"{key}_q", placeholder="song or artist name").strip()
        if q:
            if st.session_state.get(f"{key}_lq") != q:
                st.session_state[f"{key}_lq"], st.session_state[f"{key}_off"] = q, 0
            off = st.session_state[f"{key}_off"]
            try:
                items = sp_search(q, off, cid, secret)
            except requests.HTTPError as e:
                items = []
                st.error(f"Spotify search failed (HTTP {e.response.status_code}). Check the Client ID/Secret in Secrets. "
                         "Development-mode apps also need the app owner to have Spotify Premium.")
            except Exception as e:
                items = []
                st.error(f"Could not reach Spotify: {e}")
            if items:
                pick = st.selectbox("Results", range(len(items)), key=f"{key}_pick",
                                    format_func=lambda i: f"{items[i]['name']} — {', '.join(a['name'] for a in items[i]['artists'])}")
                link = items[pick]["external_urls"]["spotify"]
                b1, b2, _ = st.columns([1, 1, 4])
                if b1.button("← Prev", key=f"{key}_prev", disabled=off == 0):
                    st.session_state[f"{key}_off"] = max(0, off - 10)
                    st.rerun()
                if b2.button("Next →", key=f"{key}_next"):
                    st.session_state[f"{key}_off"] = off + 10
                    st.rerun()
            elif q and not items:
                st.caption("No results.")
    else:
        st.info("Search is off. Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in Streamlit Secrets to enable it "
                "(see README). You can still paste a link below.")
    pasted = st.text_input("…or paste a Spotify link", key=f"{key}_link", placeholder="https://open.spotify.com/track/…").strip()
    link = pasted or link
    if link:
        if sp_embed(link):
            st.code(link, language=None)
            st.caption("Copy this link into the Studio tab's Spotify box. Spotify plays for reference only – to use the song "
                       "in an exported video or to transcribe it, add its audio file.")
        else:
            st.warning("That doesn't look like a Spotify link. Use Share → Copy link in Spotify.")


def stamp(t: float) -> str:
    return f"[{int(t // 60):02d}:{t % 60:05.2f}]"


tab_studio, tab_lyrics, tab_spotify = st.tabs(["🎬 Studio", "🎤 Lyrics AI (Whisper)", "🎧 Spotify"])

with tab_studio:
    components.html(studio_html(), height=1000, scrolling=True)

with tab_lyrics:
    st.subheader("Auto lyrics + timing")
    st.caption("Upload a song or video. Whisper transcribes it and returns timed lines you can paste into the Lyrics Video Maker "
               "(or save as .lrc and use “Load .lrc”). Sung lyrics can contain mistakes, so always proofread.")
    with st.expander("🎧 Spotify (search & listen while you work on lyrics)"):
        spotify_panel("ly")
    c1, c2 = st.columns(2)
    size = c1.selectbox("Model", ["tiny", "base", "small"], index=1, help="Bigger = more accurate but slower. Free Streamlit hosting works best with tiny/base.")
    lang = c2.selectbox("Language", ["Auto-detect", "en", "ta", "hi", "te", "ml", "kn", "es", "fr"])
    up = st.file_uploader("Audio or video file", type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "mov", "webm"])
    if up and st.button("Transcribe", type="primary"):
        with tempfile.NamedTemporaryFile(suffix=pathlib.Path(up.name).suffix, delete=False) as f:
            f.write(up.getbuffer())
        try:
            model = load_model(size)
            audio = decode_audio_ffmpeg(f.name)
            segs, info = model.transcribe(audio, language=None if lang == "Auto-detect" else lang,
                                          word_timestamps=True, vad_filter=True)
        except Exception as e:
            st.error(f"Transcription failed: {e}")
            st.stop()
        finally:
            try:
                os.unlink(f.name)
            except OSError:
                pass
        bar, lines, words, rows = st.progress(0.0, "Transcribing…"), [], [], []
        for s in segs:
            lines.append(f"{stamp(s.start)} {s.text.strip()}")
            rows.append((s.start, s.end, s.text.strip()))
            words += [{"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)} for w in (s.words or [])]
            bar.progress(min(1.0, s.end / max(info.duration, 1)))
        bar.empty()
        st.session_state["lrc"], st.session_state["words"] = "\n".join(lines), words
        st.session_state["srt"] = "\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n" for i, (a, b, t) in enumerate(rows, 1))
        st.success(f"Done · detected language: {info.language}")
    if "lrc" in st.session_state:
        st.text_area("Timed lyrics (copy into PIXORA → Lyrics Video Maker)", st.session_state["lrc"], height=280)
        d1, d2, d3 = st.columns(3)
        d1.download_button("💾 Save .lrc", st.session_state["lrc"], "lyrics.lrc")
        d2.download_button("💾 Save .srt (subtitles)", st.session_state.get("srt", ""), "lyrics.srt")
        d3.download_button("💾 Save word timings (.json)", json.dumps(st.session_state["words"], ensure_ascii=False, indent=1), "words.json")
        with st.expander("Word-by-word timings"):
            st.dataframe(st.session_state["words"], use_container_width=True)

with tab_spotify:
    st.subheader("Spotify search & player")
    spotify_panel("tab")
