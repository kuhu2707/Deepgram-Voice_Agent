# Voice Appointment Booking Agent

A voice-controlled AI assistant that listens to the user, understands appointment details using natural speech, and books events in **Google Calendar**.

Built with:
- **Deepgram** (realtime Speech-to-Text; optional TTS via `pyttsx3`)
- **OpenAI GPT** (optional: reasoning / function calling for advanced intent handling)
- **Google Calendar API** (event creation)
- **Python** (async/websocket + helper scripts)

---

## ✨ Features
- Real-time voice interaction
- Understands natural phrases like “today at 6 PM”
- Auto-detects dates/times in **IST (Asia/Kolkata)** by default
- Books appointments directly in Google Calendar (via API)
- Sends spoken or printed confirmation with event link (when available)
- Avoids scheduling past dates automatically

---

## 🔧 Setup

These instructions assume Windows PowerShell and a project virtual environment (recommended `.venv`). Adjust commands for other shells/OS.

### 1) Create & activate venv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

Using `uv` (optional):

```powershell
uv add dateparser deepgram-sdk openai google-auth google-auth-oauthlib google-api-python-client pyttsx3 pyaudio websocket-client requests
```

Or with `pip` inside the venv:

```powershell
python -m pip install --upgrade pip
python -m pip install dateparser deepgram-sdk openai google-auth google-auth-oauthlib google-api-python-client pyttsx3 pyaudio websocket-client requests
```

Notes:
- `pyaudio` on Windows may require prebuilt wheels (use `pipwin` or download a wheel) if building from source fails.
- If you used `uv` earlier, dependencies may be recorded in `uv.lock`.

### 3) Google Calendar API setup (OAuth)

1. Go to the Google Cloud Console and create a new project (or use an existing one).
2. Enable the **Google Calendar API** for the project.
3. Create OAuth 2.0 credentials:
   - Credentials -> Create Credentials -> OAuth client ID
   - Choose **Desktop app** (or Web if you plan a web flow)
   - Download the resulting `credentials.json` and place it in the project root (or a secure path).
4. The app must run an OAuth flow to obtain a `token.json` (access/refresh tokens). Typical helper code uses `google-auth-oauthlib.flow.InstalledAppFlow` to produce `token.json`.

Notes: the repository does not include OAuth helper code by default — if you want, I can add a small `auth_google.py` helper that obtains and stores `token.json` for you.

### 4) Environment variables

Set the following before running (PowerShell example):

```powershell
$env:DEEPGRAM_API_KEY = "your_deepgram_key"
$env:OPENAI_API_KEY = "your_openai_key"  # optional if using GPT features
```

Keep `credentials.json` (Google OAuth client) in the project and run the OAuth helper to generate `token.json` for API access.

### 5) Run the app

```powershell
python main.py
```

The program will stream microphone audio to Deepgram, listen for booking intents, confirm details via voice (or console), and create an event in Google Calendar when authorized.

---

## How it works (overview)

- The app streams PCM audio from your microphone to Deepgram's realtime websocket and receives transcriptions.
- When a final transcript contains a booking intent (keywords like "book", "appointment"), a parser (e.g., `dateparser`) extracts date/time.
- The app asks (voice) for attendee name and email, then creates a Calendar event via Google Calendar API.
- If OAuth is not configured, the app falls back to creating a local `.ics` file you can import into Google Calendar.

---

## Troubleshooting

- ModuleNotFoundError: No module named 'dateparser'
  - Ensure you installed `dateparser` (not `dataparser`) into the same Python interpreter you use to run `main.py`.

- `pyaudio` install fails on Windows
  - Use `pipwin install pyaudio` or download a prebuilt wheel matching your Python version and install with `pip install <wheel>`.

- Google API errors (401/insufficient permissions)
  - Ensure your `token.json` was created with the same OAuth client credentials and that the Calendar API is enabled for the project.

- Import error: cannot import name 'Deepgram'
  - The official SDK may export `DeepgramClient`. In `main.py` the import was adapted to alias `DeepgramClient` as `Deepgram` for compatibility; ensure `deepgram-sdk` is installed.

---

## Security & Privacy

- Microphone audio is sent to Deepgram's cloud service for transcription. Do not record or transmit sensitive audio without consent and awareness of where data is processed.
- Store credentials (`credentials.json`, `token.json`, and API keys) securely and do not commit them to source control. Use `.gitignore` to exclude them.

---

## Next steps I can help with

- Add an OAuth helper script (`auth_google.py`) that performs the InstalledAppFlow and saves `token.json`.
- Add a `requirements.txt` with pinned versions and a `pyproject.toml` section.
- Implement optional OpenAI GPT function-calling integration for more robust intent parsing and dialog.

If you'd like, tell me which of the next steps to add and I'll implement it.
