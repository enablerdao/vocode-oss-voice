"""
Google Speech Recognition Transcriber for Vocode
Uses the free Google Web Speech API (no API key required)
"""

import asyncio
import io
import wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import speech_recognition as sr
from pydub import AudioSegment

from vocode.streaming.models.transcriber import TranscriberConfig, Transcription
from vocode.streaming.transcriber.base_transcriber import BaseThreadAsyncTranscriber


class GoogleSRTranscriberConfig(TranscriberConfig):
    language: str = "en-US"
    energy_threshold: int = 300
    pause_threshold: float = 0.8
    phrase_time_limit: float = 5.0


class GoogleSRTranscriber(BaseThreadAsyncTranscriber[GoogleSRTranscriberConfig]):
    def __init__(self, transcriber_config: GoogleSRTranscriberConfig):
        super().__init__(transcriber_config)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = transcriber_config.energy_threshold
        self.recognizer.pause_threshold = transcriber_config.pause_threshold
        self.buffer_size = int(transcriber_config.sampling_rate * 2)  # 2 seconds buffer
        self.audio_buffer = io.BytesIO()
        self.wav_writer = None
        self._ended = False
        self._init_wav_writer()
        
    def _init_wav_writer(self):
        """Initialize WAV writer for the audio buffer"""
        self.audio_buffer = io.BytesIO()
        self.wav_writer = wave.open(self.audio_buffer, 'wb')
        self.wav_writer.setnchannels(1)
        self.wav_writer.setsampwidth(2)
        self.wav_writer.setframerate(self.transcriber_config.sampling_rate)
        
    def _run_loop(self):
        """Main processing loop for the transcriber"""
        while not self._ended:
            try:
                # Get audio chunk from input queue
                chunk = self.input_janus_queue.sync_q.get()
                
                # Write chunk to buffer
                self.wav_writer.writeframes(chunk)
                
                # Check if buffer is large enough
                if self.audio_buffer.tell() >= self.buffer_size:
                    # Process the audio
                    self._process_audio()
                    
            except Exception as e:
                print(f"Error in transcription loop: {e}")
                
    def _process_audio(self):
        """Process accumulated audio buffer"""
        try:
            # Close current WAV writer
            self.wav_writer.close()
            
            # Seek to beginning of buffer
            self.audio_buffer.seek(0)
            
            # Convert to AudioSegment
            audio_segment = AudioSegment.from_wav(self.audio_buffer)
            
            # Convert to speech_recognition AudioData
            audio_data = sr.AudioData(
                audio_segment.raw_data,
                sample_rate=audio_segment.frame_rate,
                sample_width=audio_segment.sample_width
            )
            
            # Try to recognize speech
            try:
                text = self.recognizer.recognize_google(
                    audio_data, 
                    language=self.transcriber_config.language
                )
                
                if text:
                    # Send transcription
                    self.produce_nonblocking(
                        Transcription(
                            message=text,
                            confidence=0.9,  # Google doesn't provide confidence
                            is_final=True
                        )
                    )
                    
            except sr.UnknownValueError:
                # No speech detected
                pass
            except sr.RequestError as e:
                print(f"Google Speech Recognition error: {e}")
                
        except Exception as e:
            print(f"Error processing audio: {e}")
            
        finally:
            # Reset buffer and WAV writer
            self._init_wav_writer()
            
    async def terminate(self):
        """Clean up resources"""
        self._ended = True
        if self.wav_writer:
            self.wav_writer.close()