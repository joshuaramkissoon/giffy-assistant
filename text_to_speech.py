import io
import json
import logging
import keyboard
from os import getenv
from pydub import AudioSegment
import requests
from enum import Enum
import sounddevice as sd
import threading
from typing import Optional

from speech_to_text import AudioFormat

ELABS_BASE_URL = "https://api.elevenlabs.io"
AUDIO_PLAYER_STOP_KEY = 'r'
DEFAULT_SAMPLE_RATE = 44100 # Hz

class Voice(Enum):
    BELLA = "EXAVITQu4vr4xnSDxMaL"


class AudioPlayer:
    def __init__(self, stop_key: str = AUDIO_PLAYER_STOP_KEY):
        self.stop_key = stop_key
        self.stop_thread = None
        self.play_thread = None
        self.stop_playback = threading.Event()
        sd.default.samplerate = DEFAULT_SAMPLE_RATE
        
    
    def _play_audio(self, audio_bytes: bytes, audio_format: AudioFormat):
        logging.info("Starting audio playback")
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format.value)
        raw_audio_data = audio.get_array_of_samples()
        sd.play(raw_audio_data, blocking=True)
        logging.info('Finished audio playback')
        self.stop_playback.set()
        
        
    def _stop_playback(self):
        def _stop():
            logging.info("Stopping audio playback")
            self.stop_playback.set()
            sd.stop()
            
        hk = keyboard.add_hotkey(self.stop_key, _stop)
        logging.info('waiting for stop playback')
        self.stop_playback.wait()
        logging.info('stop playback')
        
        keyboard.remove_hotkey(hk)
        
        
    def play(self, file_path: Optional[str] = None, audio_bytes: Optional[bytes] = None, audio_format: Optional[AudioFormat] = AudioFormat.MP3):
        """Start playback of the audio specified either by a file path or a byte buffer.

        This method starts 2 threads: one for playback and one for monitoring user input to prematurely stop playback using the stop key.
        Args:
            file_path (Optional[str]): File path to play audio from.
            audio_bytes (Optional[bytes]): Audio as a buffer of bytes.
        """
        if not file_path and not audio_bytes:
            raise RuntimeError("Must specify filepath or provide audio as a byte buffer")

        _audio_bytes = audio_bytes if audio_bytes else None
        if file_path:
            with open(file_path, 'rb') as f:
                _audio_bytes = f.read()
        
        # Start the thread listening for stop key
        self.stop_thread = threading.Thread(target=self._stop_playback)
        self.stop_thread.start()
        
        # Start thread to play audio
        self.play_thread = threading.Thread(target=self._play_audio, args=(_audio_bytes, audio_format))
        self.play_thread.start()

        self.play_thread.join()
        self.stop_thread.join()
        
        # Cleanup threads
        self.stop_thread = None
        self.play_thread = None
        

class TextToSpeechHandler: 
    def __init__(self):
        self._api_key = getenv("ELEVENLABS_API_KEY")
        self.audio_player = AudioPlayer()
    
    def _get_versioned_uri_path(self, api_version: int, resource: str):
        return f"{ELABS_BASE_URL}/v{api_version}/{resource}"
    
    def _get_api_key_params(self):
        return {"xi-api-key": self._api_key}
    
    def to_speech(self, text: str, voice: Voice = Voice.BELLA) -> None:
        """Convert the given text to speech and play the result in the optionally provided voice.

        Args:
            text (str): Text to convert to speech
            voice (Optional[Voice]): Eleven Labs voice ID. Defaults to Voice.BELLA.
        """
        uri_path = f"text-to-speech/{voice.value}"
        url = self._get_versioned_uri_path(1, uri_path)
        body = {
            "text": text,
            "voice_settings": {
                "stability": 0,
                "similarity_boost": 0
            }
        }
        logging.info(f"Sending to_speech request, text={text}")
        response = requests.post(url, data=json.dumps(body), headers=self._get_api_key_params())
        if response.status_code != 200:
            error = response.json().get("detail")
            logging.error(f"Unsuccessful response, status_code={response.status_code}, error={error}")
            return None
        logging.info("Fetched speech response, playing audio")
        self.audio_player.play(audio_bytes=response.content, audio_format=AudioFormat.MP3)