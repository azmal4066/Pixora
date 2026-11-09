# PIXORA – Creative Studio
Streamlit app: `app.py` (Studio + Whisper lyrics), `pixora/` (the editor), Supabase for login & project sync.
Run locally: `pip install -r requirements.txt && streamlit run app.py`

- Spotify player: paste a song/playlist link in the Audio Library, Video, Music video and Lyrics video editors, and in the Lyrics AI tab (listening/reference only).
- Save: the 💾 button (top-right, or Ctrl+S) saves the current editor; "Save all" saves every unsaved editor.

## Spotify search setup (optional)
1. https://developer.spotify.com/dashboard → Create app (Redirect URI can be `http://127.0.0.1:8501`, API: Web API). Spotify currently requires the app owner to have Premium for Development Mode apps.
2. Copy Client ID + Client Secret into Streamlit **Secrets** (see `.streamlit/secrets.toml.example`). Never commit secrets.toml.
3. Open the 🎧 Spotify tab (or the Spotify box in 🎤 Lyrics AI) and search. Results show 10 per page.
