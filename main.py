import asyncio
import websockets
from flask import Flask, request, jsonify
from threading import Thread

DEEPGRAM_KEY = "606fec08de35194cc8ac18e7517ce0bc2e2283c1"
DG_URL = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000"

app = Flask(__name__)

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    raw_audio = request.data
    transcription = asyncio.run(send_to_deepgram(raw_audio))  # Get transcription
    return jsonify({"transcription": transcription})  # Return transcription as JSON

async def send_to_deepgram(raw_audio):
    try:
        async with websockets.connect(
            DG_URL,
            extra_headers={"Authorization": f"Token {DEEPGRAM_KEY}"}
        ) as ws:
            await ws.send(raw_audio)
            while True:
                msg = await ws.recv()  # Wait for the response from Deepgram
                print("📝 Transcript:", msg)  # Log the response
                # Here, extract the transcription from the message
                transcript = extract_transcription(msg)
                if transcript:
                    return transcript  # Return the transcription to the Flask app
    except Exception as e:
        print(f"❌ Error: {e}")
        return "Error in transcription."

def extract_transcription(msg):
    try:
        # Extract the transcription from the message
        data = json.loads(msg)  # Assuming msg is JSON
        transcript = data.get('channel', {}).get('alternatives', [{}])[0].get('transcript', '')
        return transcript
    except Exception as e:
        print(f"❌ Error extracting transcription: {e}")
        return None

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Run the Flask server in a separate thread
Thread(target=run_flask).start()
