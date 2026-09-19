import os
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

try:
    from piper import PiperVoice
    import lameenc
except ImportError as e:
    PiperVoice = None
    lameenc = None
    _import_error = str(e)

MODEL_DIR = Path("/tmp/piper_models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

VOICE_MODELS = {
    "en_US-lessac-medium": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "size_mb": 48
    },
    "en_US-ryan-high": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json",
        "size_mb": 120
    },
    "en_US-kathleen-low": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/kathleen/low/en_US-kathleen-low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/kathleen/low/en_US-kathleen-low.onnx.json",
        "size_mb": 15
    },
    "en_GB-alan-low": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/low/en_GB-alan-low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/low/en_GB-alan-low.onnx.json",
        "size_mb": 15
    },
    "en_GB-southern_english_female-low": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/southern_english_female/low/en_GB-southern_english_female-low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/southern_english_female/low/en_GB-southern_english_female-low.onnx.json",
        "size_mb": 15
    },
}

_voice_cache = {}

def download_file(url, dest_path):
    import urllib.request
    req = urllib.request.Request(url, headers={'User-Agent': 'Piper-TTS-Vercel/1.0'})
    with urllib.request.urlopen(req, timeout=120) as response, open(dest_path, 'wb') as f:
        f.write(response.read())

def get_voice(voice_name):
    if voice_name in _voice_cache:
        return _voice_cache[voice_name]

    if voice_name not in VOICE_MODELS:
        raise ValueError(f"Unknown voice: {voice_name}")

    model_info = VOICE_MODELS[voice_name]
    model_path = MODEL_DIR / f"{voice_name}.onnx"
    config_path = MODEL_DIR / f"{voice_name}.onnx.json"

    if not model_path.exists():
        download_file(model_info["url"], model_path)
    if not config_path.exists():
        download_file(model_info["config_url"], config_path)

    voice = PiperVoice.load(str(model_path), config_path=str(config_path))
    _voice_cache[voice_name] = voice
    return voice

def wav_to_mp3(wav_data, sample_rate=22050):
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(128)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(1)
    encoder.set_quality(2)
    mp3_data = encoder.encode(wav_data)
    mp3_data += encoder.flush()
    return mp3_data

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path not in ('/api/tts', '/api'):
            self.send_error(404, 'Not Found')
            return

        if PiperVoice is None or lameenc is None:
            self.send_json(500, {'detail': f'Missing dependencies: {_import_error}'})
            return

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_json(400, {'detail': 'Empty request body'})
            return

        try:
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json(400, {'detail': 'Invalid JSON'})
            return

        text = body.get('text', '').strip()
        voice_name = body.get('voice', 'en_US-lessac-medium')

        if not text:
            self.send_json(400, {'detail': 'Text is required'})
            return
        if len(text) > 10000:
            self.send_json(400, {'detail': 'Text exceeds 10,000 character limit'})
            return
        if voice_name not in VOICE_MODELS:
            self.send_json(400, {'detail': 'Invalid voice selected'})
            return

        try:
            voice = get_voice(voice_name)
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
                wav_path = tmp_wav.name
            
            voice.synthesize(text, wav_path)
            
            with open(wav_path, 'rb') as f:
                wav_data = f.read()
            
            os.unlink(wav_path)
            
            mp3_data = wav_to_mp3(wav_data, voice.config.sample_rate)
            
            self.send_response(200)
            self.send_header('Content-Type', 'audio/mpeg')
            self.send_header('Content-Length', str(len(mp3_data)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(mp3_data)

        except Exception as e:
            self.send_json(500, {'detail': f'Generation failed: {str(e)}'})

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        self.send_error(405, 'Method Not Allowed')