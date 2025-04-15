import asyncio
import websockets
import requests
from flask import Flask, request, Response
from threading import Thread

DEEPGRAM_KEY = "606fec08de35194cc8ac18e7517ce0bc2e2283c1"
DG_URL = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000"

app = Flask(__name__)

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    raw_audio = request.data
    # Start the async task using asyncio
    asyncio.run(send_to_deepgram(raw_audio))
    return Response("OK", status=200)

async def send_to_deepgram(raw_audio):
    print("🔄 Connecting to Deepgram...")
    try:
        async with websockets.connect(
            DG_URL,
            extra_headers={"Authorization": f"Token {DEEPGRAM_KEY}"}
        ) as ws:
            await ws.send(raw_audio)
            print("📤 Audio sent.")
            while True:
                msg = await ws.recv()  # Wait for response from Deepgram
                print("📝 Transcript:", msg)  # Log the response
    except Exception as e:
        print(f"❌ Error: {e}")

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Start Flask in one thread, asyncio loop in another
Thread(target=run_flask).start()

# Test by uploading the audio directly here (for testing, outside Flask)
file_path = r"C:\Users\adwai\Downloads\ElevenLabs_2025-04-13T14_21_55_Rachel_pre_sp100_s50_sb75_se0_b_m2.wav"

with open(file_path, "rb") as f:
    audio = f.read()

res = requests.post("https://robot-0duk.onrender.com/upload-audio", data=audio)

print("Status Code:", res.status_code)
print("Response:", res.text)
