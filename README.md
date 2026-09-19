# Piper TTS Voiceover Generator

A fully open-source, offline text-to-speech web app using **Piper TTS** (MIT licensed), deployable to Vercel's free Hobby plan. No paid APIs, no external services — safe for commercial/monetized YouTube use.

## Features

- Text input up to 10,000 characters with live character counter
- 5 high-quality English voices (US/UK, male/female, varying quality/size)
- Generates MP3 via Piper TTS + LAME encoder (pure Python)
- Models downloaded on-demand to `/tmp` (cached across warm invocations)
- 60s function timeout for long text generation
- Clean, responsive UI — no frameworks

## Project Structure

```
tts-piper/
├── index.html          # Frontend (single page)
├── api/
│   └── tts.py          # Vercel Python serverless function
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
└── README.md
```

## Voice Models (auto-downloaded on first use)

| Voice | Region | Gender | Quality | Size | Best For |
|-------|--------|--------|---------|------|----------|
| `en_US-lessac-medium` | US | Male | Medium | ~48 MB | General purpose, balanced |
| `en_US-ryan-high` | US | Male | High | ~120 MB | Premium quality, expressive |
| `en_US-kathleen-low` | US | Female | Low | ~15 MB | Fast, small footprint |
| `en_GB-alan-low` | UK | Male | Low | ~15 MB | British male, concise |
| `en_GB-southern_english_female-low` | UK | Female | Low | ~15 MB | British female |

All models from [Rhasspy Piper Voices](https://huggingface.co/rhasspy/piper-voices) (MIT/CC-BY licensed).

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install system dependencies (macOS)
brew install portaudio  # for piper-tts audio backend

# Run local test server
cd api
python -m http.server 8000
```

Then open `index.html` directly in browser, or serve static files:
```bash
python -m http.server 3000
```

**Note**: Local testing requires the voice models to download on first API call.

## Deploy to Vercel

### Prerequisites
- Git repository (GitHub, GitLab, Bitbucket)
- Vercel account (free Hobby plan)

### Steps

1. **Push this folder to a Git repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Import in Vercel**
   - Go to https://vercel.com/new
   - Select your repository
   - Vercel auto-detects Python from `vercel.json`
   - Click **Deploy**

3. **Wait for build** — first deployment installs `piper-tts`, `onnxruntime`, `lameenc`

### Vercel Configuration Details

- **`vercel.json`** sets `maxDuration: 60` (Hobby plan maximum)
- **`requirements.txt`** pins:
  - `piper-tts==1.2.0` — core TTS engine
  - `lameenc==1.6.1` — pure Python MP3 encoder (no ffmpeg needed)
  - `onnxruntime==1.18.0` — inference runtime
- Models download to `/tmp` (ephemeral, persists across warm invocations)
- First invocation per voice: +10-30s for model download
- Subsequent invocations: ~2-5s for generation

## Limits & Considerations

| Limit | Value |
|-------|-------|
| Vercel Hobby bandwidth | 100 GB/month |
| Vercel Hobby invocations | 1,000/day |
| Function timeout | 60 seconds |
| Deployment package | 50 MB (compressed) |
| `/tmp` storage | 512 MB |
| Max text length | 10,000 chars |

**Tips for reliability:**
- Use `en_US-lessac-medium` or low-quality voices for faster cold starts
- Keep text under ~5,000 chars for consistent <30s generation
- Warm the function by hitting `/api/tts` after deploy

## Error Handling

- Empty text → 400 validation error
- Text > 10,000 chars → 400 validation error
- Invalid voice → 400 validation error
- Model download failure → 500 with details
- Generation timeout → 504 (Vercel) or 500
- All errors displayed in UI

## Commercial Use

✅ **Fully permitted** — all components MIT/CC-BY licensed:
- Piper TTS: MIT
- Piper Voices: CC-BY 4.0 (attribution required)
- lameenc: LGPL (dynamic linking via Python bindings)
- onnxruntime: MIT

**Attribution** (for YouTube description):
> Voice synthesis by Piper TTS (https://github.com/rhasspy/piper), voices by Rhasspy (https://huggingface.co/rhasspy/piper-voices)

## Troubleshooting

**"Missing dependencies" error**
- Check Vercel build logs for pip install failures
- Ensure `requirements.txt` versions are compatible

**Timeout on first request**
- Model downloading takes 10-30s on cold start
- Subsequent requests are fast (model cached in `/tmp`)
- Consider pre-warming with a cron job

**"No space left on device"**
- `/tmp` limited to 512 MB
- High-quality models (ryan-high: 120 MB) + cache may fill it
- Use lower-quality voices if needed

**Audio quality issues**
- Piper outputs 22.05 kHz mono
- MP3 encoded at 128 kbps CBR
- For higher quality, modify `lameenc` settings in `tts.py`

## Adding More Voices

1. Find model at https://huggingface.co/rhasspy/piper-voices/tree/main
2. Add entry to `VOICE_MODELS` in `api/tts.py`:
   ```python
   "voice-id": {
       "url": "https://huggingface.co/.../model.onnx",
       "config_url": "https://huggingface.co/.../model.onnx.json",
       "size_mb": 50
   },
   ```
3. Add `<option>` to `index.html` select dropdown
4. Redeploy

## License

MIT — see individual component licenses above.