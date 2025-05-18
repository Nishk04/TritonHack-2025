import asyncio
import os
import pyaudio
import requests
import google.generativeai as genai
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# API keys
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

print(f"Loaded Deepgram API Key: {DEEPGRAM_API_KEY}")
print(f"Loaded Google API Key: {GOOGLE_API_KEY}")

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
timeOutTime = 30

# Transcript buffer and category state
transcript_buffer = []
last_processed = datetime.now()
category_state = {
    "Emergency Type": None,
    "Address": None,
    "Condition": None,
    "Time of emergency": None
}

# Configure Gemini model
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

async def process_buffer():
    global transcript_buffer, last_processed
    while True:
        await asyncio.sleep(2)
        if transcript_buffer and (datetime.now() - last_processed).total_seconds() >= 2:
            text = " ".join(transcript_buffer).strip()
            if text:
                print(f"\nProcessing buffer: {text}")
                try:
                    prompt = f"""
                    Analyze the following text and extract words or phrases that match the following categories:
                    - Emergency Type: Identify types of emergencies (e.g., fire, medical, crime).
                    - Address: Identify any address-related information, institutions, street names, or city names. (e.g., 11569 Swan Lake Drive) Look up the rest of the info about the City, State, and zip code and separate it with commas as shown in the example below.
                    - Condition: Identify health status or emotional state (e.g., injured, unconscious, panicked).
                    - Time of emergency: Identify time-related information (e.g., morning, evening, specific times like '5:30 A.M.' always have a space between the time (5:30) and the type (A.M. or P.M.)).
                    Return the results in a structured format, e.g.:
                    Emergency Type: fire
                    Address: 11569 Swan Lake Dr, San Diego, CA 92131
                    Condition: injured
                    Time of emergency: 5:30 A.M.
                    If no matches, return "None" for that category.
                    Text: "{text}"
                    """
                    response = model.generate_content(prompt)
                    if response.text.strip():
                        print(f"New Matches:\n{response.text}")
                        for line in response.text.split("\n"):
                            if ":" in line:
                                category, value = map(str.strip, line.split(":", 1))
                                if category in category_state and value != "None" and value:
                                    category_state[category] = value
                    else:
                        print("New Matches: None")
                except Exception as e:
                    print(f"Error querying Google AI Studio: {e}")
            print("Current State: " + ", ".join(f"{k}: {v if v else 'None'}" for k, v in category_state.items()))
            transcript_buffer = []
            last_processed = datetime.now()

async def transcribe_audio():
    try:
        if not DEEPGRAM_API_KEY or not GOOGLE_API_KEY:
            raise ValueError("API keys are not set")

        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        dg_connection = deepgram.listen.websocket.v("1")

        def on_message(self, result, **kwargs):
            transcript = result.channel.alternatives[0].transcript
            if transcript.strip():
                print(f"Transcript: {transcript}")
                transcript_buffer.append(transcript)

        def on_open(self, open, **kwargs):
            print("Connection opened")

        def on_error(self, error, **kwargs):
            print(f"Error Details: {error}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        options = LiveOptions(
            model="nova-3",
            language="en",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=RATE
        )

        dg_connection.start(options)

        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        print("Listening... Speak into your microphone (will stop after ~30 seconds)")

        buffer_task = asyncio.create_task(process_buffer())

        try:
            async def stream_audio():
                while True:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    dg_connection.send(data)
                    await asyncio.sleep(0.01)

            await asyncio.wait_for(stream_audio(), timeout=timeOutTime)

        except asyncio.TimeoutError:
            print("\n30-second timeout reached. Stopping...")
        except KeyboardInterrupt:
            print("\nManually stopped by user...")
        finally:
            buffer_task.cancel()
            dg_connection.finish()
            stream.stop_stream()
            stream.close()
            audio.terminate()

            print("Final State: " + ", ".join(f"{k}: {v if v else 'None'}" for k, v in category_state.items()))
            
            # Send to Flask server as JSON
            try:
                print("Sending data to Flask server...")
                response = requests.post("http://127.0.0.1:8000/new_incident", json={
                    "title": category_state["Emergency Type"],
                    "location": category_state["Address"],
                    "condition": category_state["Condition"],
                    "time": category_state["Time of emergency"]
                })
                print("Server response:", response.json())
            except Exception as e:
                print("Error sending incident to server:", e)

    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(transcribe_audio())

def run_transcriber():
    asyncio.run(transcribe_audio())