import os
import json
import asyncio
import websockets
import requests
from flask import Flask, request, send_file, jsonify
from threading import Thread
from gtts import gTTS  # Google Text-to-Speech

# Replace with your real keys
DEEPGRAM_KEY = "606fec08de35194cc8ac18e7517ce0bc2e2283c1"
GEMINI_API_KEY = "AIzaSyACZZTQxREALZ2idltCKXzFI9JUG8_aWp8"
DG_WS_URL = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000"

app = Flask(__name__)

# Accepts audio from ESP32 and returns audio response
@app.route("/esp32-audio", methods=["POST"])
def handle_esp32_audio():
    audio_data = request.data

    # Step 1: Transcribe via Deepgram WebSocket
    transcription = asyncio.run(transcribe_audio(audio_data))
    if not transcription:
        return jsonify({"error": "Could not transcribe"}), 400

    print("Transcribed:", transcription)

    # Step 2: Send to Gemini
    gemini_reply = get_gemini_response(transcription)
    print("Gemini:", gemini_reply)

    # Step 3: Convert to TTS
    tts_path = "response.mp3"
    tts = gTTS(gemini_reply)
    tts.save(tts_path)

    # Step 4: Send back audio
    return send_file(tts_path, mimetype="audio/mpeg")

# WebSocket-based Deepgram transcription
async def transcribe_audio(raw_audio):
    try:
        async with websockets.connect(
            DG_WS_URL,
            extra_headers={"Authorization": f"Token {DEEPGRAM_KEY}"}
        ) as ws:
            await ws.send(raw_audio)
            while True:
                msg = await ws.recv()
                print("📝 Raw WS Msg:", msg)
                data = json.loads(msg)
                text = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                if text:
                    return text
    except Exception as e:
        print("❌ Deepgram error:", e)
        return None

# Gemini API call
def get_gemini_response(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        res = requests.post(url, headers=headers, params=params, json=data)
        res_json = res.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return "Sorry, Gemini failed."

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Start Flask server
Thread(target=run_flask).start()
