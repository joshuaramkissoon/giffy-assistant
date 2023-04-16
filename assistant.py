import logging
import keyboard
from speech_to_text import AudioCapture, SpeechToTextHandler
from text_to_speech import TextToSpeechHandler
import threading

STOP_KEY = 'q'

class GiffyAssistant:
    def __init__(self, agent):
        self.agent = agent
        self.audio_capture = AudioCapture()
        self.speech_to_text_handler = SpeechToTextHandler()
        self.text_to_speech_handler = TextToSpeechHandler()
    
    
    def _run(self):
        while True:
            # Start listening to user
            self.audio_capture.await_capture()
            if self.audio_capture.has_audio():
                user_text = self.speech_to_text_handler.to_text(self.audio_capture.audio())
            else:
                continue
            
            # Pass input to LLM
            agent_response = self.agent.ask(user_text)
            self.text_to_speech_handler.to_speech(agent_response)
        
    
    def start(self):
        logging.info(f"Starting giffy-assistant, press {STOP_KEY} to stop.")
        assistant_thread = threading.Thread(target=self._run)
        assistant_thread.daemon = True
        assistant_thread.start()
        
        keyboard.wait(STOP_KEY)
        logging.info("Stopping giffy-assistant.")