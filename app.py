import pathlib, re, tempfile, streamlit as st
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


def stamp(t: float) -> str:
    return f"[{int(t // 60):02d}:{t % 60:05.2f}]"


tab_studio, tab_lyrics = st.tabs(["🎬 Studio", "🎤 Lyrics AI (Whisper)"])

with tab_studio:
    components.html(studio_html(), height=1000, scrolling=True)

with tab_lyrics:
    st.subheader("Auto lyrics + timing")
    st.caption("Upload a song or video. Whisper transcribes it and returns timed lines you can paste into the Lyrics Video Maker "
               "(or save as .lrc and use “Load .lrc”). Sung lyrics can contain mistakes, so always proofread.")
    c1, c2 = st.columns(2)
    size = c1.selectbox("Model", ["tiny", "base", "small"], index=1, help="Bigger = more accurate but slower. Free Streamlit hosting works best with tiny/base.")
    lang = c2.selectbox("Language", ["Auto-detect", "en", "ta", "hi", "te", "ml", "kn", "es", "fr"])
    up = st.file_uploader("Audio or video file", type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "mov", "webm"])
    if up and st.button("Transcribe", type="primary"):
        with tempfile.NamedTemporaryFile(suffix=pathlib.Path(up.name).suffix, delete=False) as f:
            f.write(up.getbuffer())
        model = load_model(size)
        segs, info = model.transcribe(f.name, language=None if lang == "Auto-detect" else lang,
                                      word_timestamps=True, vad_filter=True)
        bar, lines, words = st.progress(0.0, "Transcribing…"), [], []
        for s in segs:
            lines.append(f"{stamp(s.start)} {s.text.strip()}")
            words += [{"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)} for w in (s.words or [])]
            bar.progress(min(1.0, s.end / max(info.duration, 1)))
        bar.empty()
        st.session_state["lrc"], st.session_state["words"] = "\n".join(lines), words
        st.success(f"Done · detected language: {info.language}")
    if "lrc" in st.session_state:
        st.text_area("Timed lyrics (copy into PIXORA → Lyrics Video Maker)", st.session_state["lrc"], height=280)
        st.download_button("Download .lrc", st.session_state["lrc"], "lyrics.lrc")
        with st.expander("Word-by-word timings"):
            st.dataframe(st.session_state["words"], use_container_width=True)
