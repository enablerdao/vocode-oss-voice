"""
Whisper.cpp Transcriber for Vocode
完全ローカルで動作する高性能音声認識
"""

import asyncio
import io
import wave
import queue
import threading
import time
import numpy as np
from typing import Optional
from pydub import AudioSegment

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from whisper_cpp_wrapper import WhisperCPPWrapper, WhisperCPPTranscriberConfig
from vocode.streaming.models.transcriber import TranscriberConfig, Transcription
from vocode.streaming.transcriber.base_transcriber import BaseThreadAsyncTranscriber


class VocodeWhisperCPPTranscriberConfig(TranscriberConfig):
    """Vocode用Whisper.cpp設定"""
    language: str = "ja"
    model_path: Optional[str] = None
    whisper_cpp_path: str = "/opt/homebrew/bin/whisper-cpp"
    translate: bool = False
    chunk_duration_seconds: float = 2.0  # 2秒ごとに処理
    silence_threshold: int = 500
    min_chunk_duration: float = 0.5


class WhisperCPPTranscriber(BaseThreadAsyncTranscriber[VocodeWhisperCPPTranscriberConfig]):
    """Whisper.cppを使用したローカル音声認識トランスクライバー"""
    
    def __init__(self, transcriber_config: VocodeWhisperCPPTranscriberConfig):
        super().__init__(transcriber_config)
        
        # Whisper.cppラッパーの初期化
        self.whisper = WhisperCPPWrapper(
            model_path=transcriber_config.model_path,
            whisper_cpp_path=transcriber_config.whisper_cpp_path,
            language=transcriber_config.language,
            translate=transcriber_config.translate,
        )
        
        # 音声処理パラメータ
        self.chunk_duration = transcriber_config.chunk_duration_seconds
        self.chunk_size = int(transcriber_config.sampling_rate * self.chunk_duration * 2)  # 16bit
        self.silence_threshold = transcriber_config.silence_threshold
        self.min_chunk_duration = transcriber_config.min_chunk_duration
        
        # バッファとキュー
        self.audio_queue = queue.Queue()
        self.current_buffer = []
        self.processing = False
        self._ended = False
        
        # 音声レベル追跡
        self.silence_counter = 0
        self.speech_detected = False
        self.max_silence_chunks = int(0.5 / (self.chunk_size / transcriber_config.sampling_rate / 2))
        
        print(f"🎤 Whisper.cpp transcriber initialized")
        print(f"   Language: {transcriber_config.language}")
        print(f"   Model: {transcriber_config.model_path}")
        
    def _run_loop(self):
        """メイン処理ループ"""
        # 処理スレッドを開始
        processing_thread = threading.Thread(target=self._process_audio_loop)
        processing_thread.daemon = True
        processing_thread.start()
        
        accumulated_audio = bytearray()
        
        while not self._ended:
            try:
                # 音声チャンクを取得
                chunk = self.input_janus_queue.sync_q.get()
                accumulated_audio.extend(chunk)
                
                # 一定サイズに達したら処理キューに送る
                if len(accumulated_audio) >= self.chunk_size:
                    # 音声データをキューに追加
                    self.audio_queue.put(bytes(accumulated_audio[:self.chunk_size]))
                    accumulated_audio = accumulated_audio[self.chunk_size:]
                    
            except Exception as e:
                print(f"Error in audio loop: {e}")
                
    def _process_audio_loop(self):
        """音声処理ループ（別スレッド）"""
        audio_buffer = io.BytesIO()
        wav_writer = wave.open(audio_buffer, 'wb')
        wav_writer.setnchannels(1)
        wav_writer.setsampwidth(2)
        wav_writer.setframerate(self.transcriber_config.sampling_rate)
        
        buffer_start_time = time.time()
        has_speech = False
        
        while not self._ended:
            try:
                # キューから音声データを取得
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # WAVファイルに書き込む
                wav_writer.writeframes(audio_data)
                
                # 音声のエネルギーレベルをチェック
                audio_segment = AudioSegment(
                    audio_data,
                    frame_rate=self.transcriber_config.sampling_rate,
                    sample_width=2,
                    channels=1
                )
                
                # RMSエネルギーを計算
                rms = audio_segment.rms
                
                if rms > self.silence_threshold:
                    has_speech = True
                    self.silence_counter = 0
                else:
                    self.silence_counter += 1
                
                # バッファの継続時間を計算
                buffer_duration = time.time() - buffer_start_time
                
                # 音声が検出され、十分な長さがある場合、または最大時間に達した場合
                should_process = (
                    (has_speech and self.silence_counter >= self.max_silence_chunks and 
                     buffer_duration >= self.min_chunk_duration) or
                    buffer_duration >= self.chunk_duration * 2
                )
                
                if should_process and audio_buffer.tell() > 0:
                    # Whisperで転写
                    asyncio.run(self._transcribe_buffer(audio_buffer, wav_writer))
                    
                    # バッファをリセット
                    audio_buffer = io.BytesIO()
                    wav_writer = wave.open(audio_buffer, 'wb')
                    wav_writer.setnchannels(1)
                    wav_writer.setsampwidth(2)
                    wav_writer.setframerate(self.transcriber_config.sampling_rate)
                    buffer_start_time = time.time()
                    has_speech = False
                    self.silence_counter = 0
                    
            except queue.Empty:
                # タイムアウト時もバッファをチェック
                if has_speech and time.time() - buffer_start_time >= self.min_chunk_duration:
                    asyncio.run(self._transcribe_buffer(audio_buffer, wav_writer))
                    
                    # バッファをリセット
                    audio_buffer = io.BytesIO()
                    wav_writer = wave.open(audio_buffer, 'wb')
                    wav_writer.setnchannels(1)
                    wav_writer.setsampwidth(2)
                    wav_writer.setframerate(self.transcriber_config.sampling_rate)
                    buffer_start_time = time.time()
                    has_speech = False
                    
            except Exception as e:
                print(f"Error in processing loop: {e}")
                
        if wav_writer:
            wav_writer.close()
            
    async def _transcribe_buffer(self, audio_buffer: io.BytesIO, wav_writer: wave.Wave_write):
        """バッファの音声を転写"""
        try:
            # WAVライターを閉じる
            wav_writer.close()
            
            # バッファの位置をリセット
            audio_buffer.seek(0)
            
            # 音声データを取得
            audio_data = audio_buffer.read()
            
            if len(audio_data) > 44:  # WAVヘッダーサイズ
                # Whisperで転写
                text = await self.whisper.transcribe_audio_data(
                    audio_data[44:],  # WAVヘッダーをスキップ
                    sample_rate=self.transcriber_config.sampling_rate
                )
                
                if text and text.strip():
                    print(f"🎤 Whisper認識: {text}")
                    
                    # 転写結果を送信
                    self.produce_nonblocking(
                        Transcription(
                            message=text.strip(),
                            confidence=0.98,  # Whisperは高精度
                            is_final=True
                        )
                    )
                    
        except Exception as e:
            print(f"Transcription error: {e}")
            
    async def terminate(self):
        """リソースのクリーンアップ"""
        self._ended = True
        if hasattr(self, 'whisper'):
            self.whisper.close()