import io
import json
import logging
from os import getenv
from pydub import AudioSegment, playback
# import pygame
import requests
from enum import Enum
import time

ELABS_BASE_URL = "https://api.elevenlabs.io"

class Voice(Enum):
    BELLA = "EXAVITQu4vr4xnSDxMaL"


class AudioPlayer:
    def play(file_path: str = None, audio_bytes: bytes = None):
        audio = None
        if file_path:
            audio = AudioSegment.from_file(file_path, format="mp3")
        elif audio_bytes:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        playback.play(audio)
        
        

class TextToSpeechHandler: 
    def __init__(self):
        self._api_key = getenv("ELEVENLABS_API_KEY")
    
    def _get_versioned_uri_path(self, api_version: int, resource: str):
        return f"{ELABS_BASE_URL}/v{api_version}/{resource}"
    
    def _get_api_key_params(self):
        return {"xi-api-key": self._api_key}
    
    def to_speech(self, text: str, voice: Voice = Voice.BELLA):
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
        AudioPlayer.play(audio_bytes=response.content)