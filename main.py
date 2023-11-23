import asyncio
import base64
import json
import pyaudio
import websockets
import time
from pynput import keyboard
from openai import OpenAI
from configure import auth_key, OPENAI_API_KEY, system_prompt, ai_model, user_name, interviewer_name

class RealtimeTranscriber:
    """
    A class to transcribe speech in real-time using AssemblyAI's WebSocket API and process the 
    transcription using OpenAI's GPT model.
    """

    # Constants for audio configuration
    FRAMES_PER_BUFFER = 3200
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WEBSOCKET_URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

    def __init__(self):
        """
        Initializes the transcriber with the specified AI model and sets up the audio stream.
        
        Args:
            ai_model: The AI model used for generating responses (default is GPT-4).
        """
        self.audio = pyaudio.PyAudio()  # Initialize the PyAudio object
        self.model = ai_model  # AI model used for OpenAI's API
        self.user_message = ""  # Stores the user's spoken message
        self.user_name = user_name  # The name of the user speaking
        self.interviewer_name = interviewer_name  # The name of the interviewer
        self.assistant_message = ""  # Stores the assistant's message
        self.messages = [{"role": "system", "content": system_prompt}]  # Initializes message history with the system prompt
        
        # Append a user note to the message history to guide GPTs response style
        self.append_message("user", "Note: Remember to always be concise, brief, straight-to-the-point...")
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)  # Initialize the OpenAI client
        
        # Open an audio stream with the specified format, channels, rate, etc.
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.FRAMES_PER_BUFFER,
            input_device_index=1  # Index of the input device (may need to be changed based on hardware)
        )
        self.transcribing = False  # Flag to track if transcription has started
        self.stop_transcription = False  # Flag to indicate when to stop transcription

    def append_message(self, role: str, message: str):
        """
        Appends a message with a specified role to the message history.

        Args:
            role: The role of the message sender (e.g., 'user' or 'assistant').
            message: The content of the message.
        """
        self.messages.append({"role": role, "content": message})

    async def send_receive(self):
        """
        Manages the sending and receiving of data via WebSocket.
        Handles the WebSocket connection and orchestrates the sending and receiving tasks.
        """
        while not self.stop_transcription:
            # Handle the WebSocket connection and catch any exceptions
            try:
                async with websockets.connect(
                    self.WEBSOCKET_URL,
                    extra_headers=(("Authorization", auth_key),),
                    ping_interval=5,
                    ping_timeout=20
                ) as websocket:
                    await asyncio.sleep(0.1)  # Short delay before starting
                    if not self.transcribing:
                        print("Press spacebar to start transcription.")

                    # Create tasks for sending audio and receiving transcripts
                    send_task = asyncio.create_task(self.send_audio(websocket))
                    receive_task = asyncio.create_task(self.receive_transcript(websocket))
                    await asyncio.gather(send_task, receive_task)
            except websockets.exceptions.ConnectionClosedError as e:
                if "Session idle for too long" not in str(e):
                    raise
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break

    async def send_audio(self, websocket):
        """
        Sends audio data to the WebSocket.
        Continuously reads audio from the stream and sends it to AssemblyAI for transcription.
        """
        while not self.stop_transcription:
            if self.transcribing:
                # Read audio data and encode it to base64
                data = self.stream.read(self.FRAMES_PER_BUFFER, exception_on_overflow=False)
                encoded_data = base64.b64encode(data).decode("utf-8")
                # Send the encoded audio data to the WebSocket
                await websocket.send(json.dumps({"audio_data": encoded_data}))
            await asyncio.sleep(0.01)  # Short delay between audio sends

    async def receive_transcript(self, websocket):
        """
        Receives and processes the transcription results.
        Listens for transcription results from AssemblyAI and processes final transcripts.
        """
        while not self.stop_transcription:
            result = await websocket.recv()  # Receive transcription result
            transcript = json.loads(result)  # Decode JSON response
            if 'text' in transcript and transcript['message_type'] == 'FinalTranscript':
                self.user_message += transcript['text']  # Append the text to the user's message
                if not self.transcribing:
                    print(f"{self.interviewer_name}: {self.user_message}\n")
                    self.append_message("user", self.user_message)
                    self.process_transcripts(self.user_message)  # Process the transcript through OpenAI
                    self.user_message = ""  # Reset the user message
            await asyncio.sleep(0.01)  # Short delay between receiving messages

    def process_transcripts(self, transcript):
        """
        Processes the transcript through OpenAI's API.
        Sends the user's transcript to OpenAI's GPT model and prints the assistant's response.
        """
        print("Processing...\n")
        print(f"{self.user_name}: ", end='', flush=True)
        # Get response from OpenAI and print it
        for content in self.get_response_from_openai(transcript):
            if content:
                print(content, end='', flush=True)
                self.assistant_message += content
        self.append_message("assistant", self.assistant_message)  # Append the assistant's response
        print("\n\nPress spacebar to continue transcription.")  # Instruction to continue transcription
        self.assistant_message = ""  # Reset the assistant message

    def get_response_from_openai(self, transcript):
        """
        Yields the response from OpenAI's API.
        Retrieves the conversation from OpenAI's API and yields the response content.
        """
        stream = self.openai_client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True
        )
        for response in stream:
            yield response.choices[0].delta.content

    def toggle_transcription(self):
        """
        Toggles the transcription on and off.
        Switches the transcription state between paused and active.
        """
        self.transcribing = not self.transcribing  # Toggle the transcribing flag
        status = "started" if self.transcribing else "paused"
        print(f"Transcription {status}. Press spacebar to toggle...\n")

    def run(self):
        """
        Starts the transcriber.
        Initializes the key listener and starts the send/receive loop.
        """
        listener = keyboard.Listener(on_press=self.on_key_press)
        listener.start()  # Start listening for key presses
        asyncio.run(self.send_receive())  # Start the send/receive loop
        listener.join()  # Join the listener thread

    def on_key_press(self, key):
        """
        Handles key press events.
        Toggles transcription on spacebar press and stops transcription on escape key press.
        """
        if key == keyboard.Key.space:
            if self.transcribing:
                time.sleep(0.3)  # Added delay to process any remaining transcription
            self.toggle_transcription()  # Toggle the transcription state
        elif key == keyboard.Key.esc:
            print("Exiting transcription.")
            self.stop_transcription = True  # Set flag to stop transcription
            return False  # Stop the listener

# Main execution
if __name__ == "__main__":
    transcriber = RealtimeTranscriber()  # Instantiate the transcriber
    transcriber.run()  # Run the transcriber
