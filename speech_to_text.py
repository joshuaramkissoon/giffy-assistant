from enum import Enum
from pydub import AudioSegment
from google.cloud import speech
import pyaudio
import wave
import io
import keyboard
import logging
import threading
from typing import Optional

# Settings
CHANNELS = 1
RATE = 44100
CHUNK = 1024
AUDIO_DATA_TYPE = pyaudio.paInt16
CAPTURE_KEY = "c"
STOP_KEY = "s"
CANCEL_KEY = "x"
DEFAULT_AUDIO_FORMAT = "mp3"

class AudioFormat(Enum):
    MP3 = "mp3"
    WAV = "wav"

class AudioCapture:
    def __init__(self, capture_key: str = CAPTURE_KEY, stop_key: str = STOP_KEY, cancel_key: str = CANCEL_KEY, channels: int = CHANNELS, rate: int = RATE, chunk: int = CHUNK, audio_data_type=AUDIO_DATA_TYPE):
        self.capture_key = capture_key
        self.stop_key = stop_key
        self.cancel_key = cancel_key
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.audio_data_type = audio_data_type
        self.is_recording = False
        self.recorded_audio: bytes = None
        self.is_cancel: bool = False
    
    def _record(self, byte_buffer):
        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Open a new stream for recording
        stream = audio.open(format=self.audio_data_type, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk)
        logging.info(f"Recording audio, press the '{self.stop_key}' key to stop and '{self.cancel_key}' to cancel.")

        frames = []

        # Record audio
        while self.is_recording:
            data = stream.read(self.chunk)
            frames.append(data)
            
        if self.is_cancel:
            logging.info("Recording cancelled.")
            byte_buffer.close()
            stream.stop_stream()
            stream.close()
            audio.terminate()
            return


        # Save the recorded audio to a buffer of bytes
        with wave.open(byte_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(audio.get_sample_size(self.audio_data_type))
            wav_file.setframerate(self.rate)
            wav_file.writeframes(b''.join(frames))

        # Reset buffer position to the beginning
        byte_buffer.seek(0)
        self.recorded_audio = byte_buffer.getvalue()
        byte_buffer.close()
        stream.stop_stream()
        stream.close()
        audio.terminate()
        logging.info(f"Finished recording audio, bytes={len(self.recorded_audio)}")
        

    def await_capture(self):
        logging.info(f"User turn: Press '{self.capture_key}' to start recording your response. Press '{self.stop_key}' to stop recording or '{self.cancel_key}' to cancel a recording.")
        self.is_recording = True
        keyboard.wait(self.capture_key)
        
        byte_buffer = io.BytesIO()
        self.recording_thread = threading.Thread(target=self._record, args=(byte_buffer,))
        self.recording_thread.start()
        
        def _handle_stop(is_cancel: bool):
            self.is_cancel = is_cancel
            self.is_recording = False
            if is_cancel:
                self.recorded_audio = None
            keyboard.remove_hotkey(stop_hk)
            keyboard.remove_hotkey(cancel_hk)
            
        stop_hk = keyboard.add_hotkey(self.stop_key, _handle_stop, args=(False,))
        cancel_hk = keyboard.add_hotkey(self.cancel_key, _handle_stop, args=(True,))
        self.recording_thread.join()

    
    def has_audio(self) -> bool:
        return self.recorded_audio is not None
    

    def audio(self, format: Optional[AudioFormat] = AudioFormat.WAV) -> bytes:
        if not self.is_recording and not self.has_audio():
            raise RuntimeError("No audio captured.")
        
        if self.is_recording:
            self.recording_thread.join()
        if not self.has_audio():
            raise RuntimeError("No audio captured.")
        
        if format == AudioFormat.WAV:
            return self.recorded_audio
        
        # Load the recorded audio as a WAV file
        audio_segment = AudioSegment.from_wav(io.BytesIO(self.recorded_audio))

        # Convert the audio to specified format
        formatted_audio = io.BytesIO()
        audio_segment.export(formatted_audio, format=format.value)
        formatted_audio.seek(0)

        return formatted_audio.getvalue()

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