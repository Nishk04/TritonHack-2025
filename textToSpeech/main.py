import asyncio
import os
import pyaudio
import google.generativeai as genai
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv
from datetime import datetime
import csv
import keyboard

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

# Buffer for collecting transcripts
transcript_buffer = []
last_processed = datetime.now()

# Categories for different factors the program is looking for
# Defaulted to none
category_state = {
    "Emergency Type": None,
    "Address": None,
    "Condition": None,
    "Time of emergency": None
}

# Google AI Studio configuration
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

async def process_buffer():
    global transcript_buffer, last_processed
    while True:
        await asyncio.sleep(2)  # Process request every 2 seconds to Gemini API
        if transcript_buffer and (datetime.now() - last_processed).total_seconds() >= 2:
            # Combine buffered transcripts
            text = " ".join(transcript_buffer)
            if text.strip():
                print(f"\nProcessing buffer: {text}")
                try:
                    # Prompt for Gemini to ask for a return that fits the category_state
                    prompt = f"""
                    Analyze the following text and extract words or phrases that match the following categories:
                    - Emergency Type: Identify types of emergencies (e.g., fire, medical, crime).
                    - Address: Identify any address-related information, institutions, street names, or city names. (eg. 11569 Swan Lake Drive) Look up the rest of the info about the City, State, and zip code and seperate it with commas as shown in the example below.
                    - Condition: Identify health status or emotional state (e.g., injured, unconscious, panicked).
                    - Time of emergency: Identify time-related information (e.g., morning, evening, specific times like '5:30 A.M.' always have a space between the time (5:30) and the type (A.M. or P.M.)).
                    Return the results in a structured format, e.g.:
                    Emergency Type: fire
                    Address: 11569 Swan Lake Dr San Diego CA 92131
                    Condition: injured
                    Time of emergency: 5:30 A.M. 
                    If no matches, return "None" for that category.
                    Text: "{text}"
                    """
                    response = model.generate_content(prompt)
                    if response.text.strip():
                        print(f"New Matches:\n{response.text}")
                        # Process Gemini response
                        for line in response.text.split("\n"):
                            if ":" in line:
                                category, value = map(str.strip, line.split(":", 1))
                                if category in category_state and value != "None" and value:
                                    category_state[category] = value
                                    # Warn if Address lacks expected components
                                    if category == "Address":
                                        if not all(x in value for x in [",", " "]) or len(value.split(",")) < 3:
                                            print(f"Warning: Address '{value}' may be incomplete (missing street, city, state, or ZIP).")
                    else:
                        print("New Matches: None")
                except Exception as e:
                    print(f"Error querying Google AI Studio: {e}")
            # Print current category state
            print("Current State: " + ", ".join(f"{k}: {v if v else 'None'}" for k, v in category_state.items()))
            # Clear buffer and update last processed time
            transcript_buffer = []
            last_processed = datetime.now()

async def check_keyboard(stop_event):
    while not stop_event.is_set():
        if keyboard.is_pressed('q'):
            print("Stopping...")
            stop_event.set()
            break
        await asyncio.sleep(0.1)  

async def transcribe_audio():
    try:
        if not DEEPGRAM_API_KEY or not GOOGLE_API_KEY:
            raise ValueError("API keys are not set")

        # Initialize Deepgram client
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        # Create a websocket connection to Deepgram
        dg_connection = deepgram.listen.websocket.v("1")

        # Define callback for handling transcription results
        def on_message(self, result, **kwargs):
            transcript = result.channel.alternatives[0].transcript
            if transcript.strip():  # Only process non-empty transcripts
                print(f"Transcript: {transcript}")
                transcript_buffer.append(transcript)

        # Define callback for connection open
        def on_open(self, open, **kwargs):
            print("Connection opened")

        # Define callback for errors
        def on_error(self, error, **kwargs):
            print(f"Error Details: {error}")

        # Register callbacks
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        # Configure Deepgram options
        options = LiveOptions(
            model="nova-3",
            language="en",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=RATE
        )

        # Start the connection
        dg_connection.start(options)

        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        print("Listening... Speak into your microphone (will stop after ~30 seconds)")

        # Start buffer processing task
        buffer_task = asyncio.create_task(process_buffer())
        # Create an event to signal stopping
        stop_event = asyncio.Event()
        # Start keyboard monitoring task
        keyboard_task = asyncio.create_task(check_keyboard(stop_event))

        # Stream audio to Deepgram with timeout
        try:
            async def stream_audio():
                while not stop_event.is_set():
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    dg_connection.send(data)
                    await asyncio.sleep(0.01)  # Prevent blocking

            await asyncio.wait_for(stream_audio(), timeout=timeOutTime)  # set timeout ~30 seconds

        except asyncio.TimeoutError:
            print("\n30-second timeout reached. Stopping...")
        except KeyboardInterrupt:
            print("\nManually stopped by user...")
        finally:
            # Clean up
            buffer_task.cancel()
            keyboard_task.cancel()
            dg_connection.finish()
            stream.stop_stream()
            stream.close()
            audio.terminate()
            # Print final category state
            print("Final State: " + ", ".join(f"{k}: {v if v else 'None'}" for k, v in category_state.items()))
            # Save final state to CSV
            with open("data.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=category_state.keys())
                writer.writeheader()
                writer.writerow({k: v if v else "None" for k, v in category_state.items()})
            print("Final state saved to data.csv")

    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(transcribe_audio())