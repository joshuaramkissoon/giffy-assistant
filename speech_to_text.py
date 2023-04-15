from google.cloud import speech
import pyaudio
import wave
import io
import keyboard
import logging
import threading

# Settings
CHANNELS = 1
RATE = 44100
CHUNK = 1024
AUDIO_FMT = pyaudio.paInt16
CAPTURE_KEY = "c"
STOP_KEY = "s"

class AudioCapture:
    def __init__(self, capture_key: str = CAPTURE_KEY, stop_key: str = STOP_KEY, channels: int = CHANNELS, rate: int = RATE, chunk: int = CHUNK, audio_format=AUDIO_FMT):
        self.capture_key = capture_key
        self.stop_key = stop_key
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.audio_format = audio_format
        self.is_recording = False
        self.recorded_audio: bytes = None

    def _record(self, byte_buffer):
        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Open a new stream for recording
        stream = audio.open(format=self.audio_format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk)

        logging.info(f"Recording audio, press the '{self.stop_key}' key to stop.")

        frames = []

        # Record audio
        while self.is_recording:
            data = stream.read(self.chunk)
            frames.append(data)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()

        # Terminate PyAudio
        audio.terminate()

        # Save the recorded audio to a buffer of bytes
        with wave.open(byte_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(audio.get_sample_size(self.audio_format))
            wav_file.setframerate(self.rate)
            wav_file.writeframes(b''.join(frames))

        # Reset buffer position to the beginning
        byte_buffer.seek(0)
        logging.info("Finished recording audio")
        

    def await_capture(self):
        logging.info(f"User turn: Press {self.capture_key} to start recording your response. Press {self.stop_key} to stop recording.")
        keyboard.wait(self.capture_key)
        
        byte_buffer = io.BytesIO()
        self.is_recording = True

        recording_thread = threading.Thread(target=self._record, args=(byte_buffer,))
        recording_thread.start()

        # Wait for the user to press the stop key
        keyboard.wait(self.stop_key)

        self.is_recording = False
        recording_thread.join()

        self.recorded_audio = byte_buffer.getvalue()
        byte_buffer.close()

    def audio(self) -> bytes:
        return self.recorded_audio

class SpeechToTextHandler:
    def __init__(self):
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
        )
        
    
    def to_text(self, audio: bytes) -> str:
        audio = speech.RecognitionAudio(content=audio)

        # Detect speech in the audio buffer
        response = self.client.recognize(config=self.config, audio=audio)
        if not response.results:
            raise RuntimeError("Unable to convert speech to text")
        
        transcript = "".join(map(lambda result: result.alternatives[0].transcript, response.results))
        logging.info(f"Successfully transcribed speech to text, transcript={transcript}")
        return transcript