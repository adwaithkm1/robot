import asyncio
import websockets
from flask import Flask, request, Response
from threading import Thread

DEEPGRAM_KEY = "606fec08de35194cc8ac18e7517ce0bc2e2283c1"
DG_URL = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000"

app = Flask(__name__)
loop = asyncio.new_event_loop()  # new loop for background tasks
asyncio.set_event_loop(loop)

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    raw_audio = request.data
    loop.create_task(send_to_deepgram(raw_audio))  # schedule the async task
    return Response("OK", status=200)

async def send_to_deepgram(raw_audio):
    print("🔄 Connecting to Deepgram...")
    async with websockets.connect(
        DG_URL,
        extra_headers={"Authorization": f"Token {DEEPGRAM_KEY}"}
    ) as ws:
        await ws.send(raw_audio)
        print("📤 Audio sent.")
        while True:
            try:
                msg = await ws.recv()
                print("📝 Transcript:", msg)
            except Exception as e:
                print("❌ WebSocket Error:", e)
                break

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Start Flask in one thread, asyncio loop in another
Thread(target=run_flask).start()
Thread(target=loop.run_forever).start()
