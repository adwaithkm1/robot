import asyncio
import websockets
import json
import requests
from flask import Flask, request, jsonify
from threading import Thread

# Replace with your Deepgram API Key
DEEPGRAM_KEY = "606fec08de35194cc8ac18e7517ce0bc2e2283c1"
DG_URL = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000"

app = Flask(__name__)

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    raw_audio = request.data  # Get the raw audio data from the request
    transcription = asyncio.run(send_to_deepgram(raw_audio))  # Get transcription
    return jsonify({"transcription": transcription})  # Return transcription as JSON

@app.route('/upload-audio-file', methods=['POST'])
def upload_audio_file():
    file = request.files['audio']  # Get the uploaded file from the form data
    file_path = f"temp_audio.wav"  # Save the file temporarily
    file.save(file_path)
    transcription = transcribe_with_deepgram(file_path)  # Get transcription from file
    return jsonify({"transcription": transcription})  # Return transcription as JSON

# WebSocket real-time transcription
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
                # Extract transcription from the WebSocket message
                transcript = extract_transcription(msg)
                if transcript:
                    return transcript  # Return the transcription to the Flask app
    except Exception as e:
        print(f"❌ Error: {e}")
        return "Error in transcription."

def extract_transcription(msg):
    try:
        # Extract the transcription from the WebSocket message
        data = json.loads(msg)  # Assuming msg is JSON
        transcript = data.get('channel', {}).get('alternatives', [{}])[0].get('transcript', '')
        return transcript
    except Exception as e:
        print(f"❌ Error extracting transcription: {e}")
        return None

# File-based transcription (HTTP POST method)
def transcribe_with_deepgram(wav_path):
    try:
        with open(wav_path, 'rb') as audio:
            response = requests.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {DEEPGRAM_KEY}",
                    "Content-Type": "audio/wav"
                },
                data=audio
            )
        if response.status_code == 200:
            # Extract the transcription from the JSON response
            return response.json()['results']['channels'][0]['alternatives'][0]['transcript']
        else:
            raise Exception(f"Deepgram Error {response.status_code}: {response.text}")
    except Exception as e:
        return f"Transcription error: {e}"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Run the Flask server in a separate thread for hosting
Thread(target=run_flask).start()

