#!/usr/bin/env python3
"""
高性能OSS音声会話デモ
- Google Speech Recognition (最適化版) - 無料音声認識
- gTTS - 無料音声合成
- OpenAI GPT-3.5 - AIエージェント
"""

import asyncio
import signal
import os
import sys
import io
import wave
import queue
import threading
import time
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
import speech_recognition as sr
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent))

from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.agent.echo_agent import EchoAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig, EchoAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import GTTSSynthesizerConfig
from vocode.streaming.models.transcriber import TranscriberConfig, Transcription
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.synthesizer.gtts_synthesizer import GTTSSynthesizer
from vocode.streaming.transcriber.base_transcriber import BaseThreadAsyncTranscriber
from pydub import AudioSegment

configure_pretty_logging()
load_dotenv()


class OptimizedGoogleSRTranscriberConfig(TranscriberConfig):
    language: str = "en-US"
    energy_threshold: int = 300
    pause_threshold: float = 0.5
    phrase_threshold: float = 0.3
    non_speaking_duration: float = 0.5
    chunk_duration_seconds: float = 0.5


class OptimizedGoogleSRTranscriber(BaseThreadAsyncTranscriber[OptimizedGoogleSRTranscriberConfig]):
    """高性能版Google Speech Recognition Transcriber"""
    
    def __init__(self, transcriber_config: OptimizedGoogleSRTranscriberConfig):
        super().__init__(transcriber_config)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = transcriber_config.energy_threshold
        self.recognizer.pause_threshold = transcriber_config.pause_threshold
        self.recognizer.phrase_threshold = transcriber_config.phrase_threshold
        self.recognizer.non_speaking_duration = transcriber_config.non_speaking_duration
        
        # オーディオバッファ設定
        self.chunk_duration = transcriber_config.chunk_duration_seconds
        self.chunk_size = int(transcriber_config.sampling_rate * self.chunk_duration)
        self.audio_queue = queue.Queue()
        self.is_processing = False
        self._ended = False
        
        # リアルタイム処理用スレッドプール
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # 音声バッファ
        self.current_buffer = []
        self.silence_counter = 0
        self.max_silence_chunks = int(1.0 / self.chunk_duration)  # 1秒の無音
        
    def _run_loop(self):
        """メイン処理ループ"""
        # 音声処理スレッドを開始
        processing_thread = threading.Thread(target=self._process_audio_loop)
        processing_thread.daemon = True
        processing_thread.start()
        
        while not self._ended:
            try:
                # 音声チャンクを取得
                chunk = self.input_janus_queue.sync_q.get()
                
                # バッファに追加
                self.current_buffer.append(chunk)
                
                # 一定サイズになったら処理キューに送る
                if len(self.current_buffer) * len(chunk) >= self.chunk_size * 2:
                    audio_data = b''.join(self.current_buffer)
                    self.audio_queue.put(audio_data)
                    self.current_buffer = []
                    
            except Exception as e:
                print(f"Error in audio loop: {e}")
                
    def _process_audio_loop(self):
        """音声処理ループ（別スレッド）"""
        accumulated_audio = io.BytesIO()
        wav_writer = wave.open(accumulated_audio, 'wb')
        wav_writer.setnchannels(1)
        wav_writer.setsampwidth(2)
        wav_writer.setframerate(self.transcriber_config.sampling_rate)
        
        speech_detected = False
        
        while not self._ended:
            try:
                # キューから音声データを取得（タイムアウト付き）
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
                
                if rms > self.transcriber_config.energy_threshold:
                    speech_detected = True
                    self.silence_counter = 0
                else:
                    self.silence_counter += 1
                
                # 音声が検出され、その後無音が続いた場合に認識を実行
                if speech_detected and self.silence_counter >= self.max_silence_chunks:
                    # 音声認識を実行
                    wav_writer.close()
                    accumulated_audio.seek(0)
                    
                    try:
                        audio_for_recognition = AudioSegment.from_wav(accumulated_audio)
                        audio_data = sr.AudioData(
                            audio_for_recognition.raw_data,
                            sample_rate=audio_for_recognition.frame_rate,
                            sample_width=audio_for_recognition.sample_width
                        )
                        
                        # Google Speech Recognitionで認識
                        text = self.recognizer.recognize_google(
                            audio_data,
                            language=self.transcriber_config.language
                        )
                        
                        if text:
                            print(f"🎤 認識: {text}")
                            # 認識結果を送信
                            self.produce_nonblocking(
                                Transcription(
                                    message=text,
                                    confidence=0.95,
                                    is_final=True
                                )
                            )
                    
                    except sr.UnknownValueError:
                        pass  # 音声が認識できなかった
                    except sr.RequestError as e:
                        print(f"Google Speech Recognition error: {e}")
                    
                    # バッファをリセット
                    accumulated_audio = io.BytesIO()
                    wav_writer = wave.open(accumulated_audio, 'wb')
                    wav_writer.setnchannels(1)
                    wav_writer.setsampwidth(2)
                    wav_writer.setframerate(self.transcriber_config.sampling_rate)
                    speech_detected = False
                    self.silence_counter = 0
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in processing loop: {e}")
                
        if wav_writer:
            wav_writer.close()
            
    async def terminate(self):
        """リソースのクリーンアップ"""
        self._ended = True
        self.executor.shutdown(wait=False)


async def main():
    """メイン関数"""
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    use_openai = bool(openai_api_key)
    
    print("=" * 60)
    print("🚀 高性能OSS音声会話デモ")
    print("=" * 60)
    print()
    print("🎤 音声認識: Google Speech Recognition (最適化版)")
    print("🔊 音声合成: gTTS (Google Text-to-Speech)")
    print(f"🤖 AI: {'OpenAI GPT-3.5' if use_openai else 'Echo Agent'}")
    print()
    print("特徴:")
    print("- リアルタイム音声認識")
    print("- 低遅延レスポンス")
    print("- 自然な会話フロー")
    print()
    
    # マイクとスピーカーの設定
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
    )
    
    # エージェントの選択
    if use_openai:
        agent = ChatGPTAgent(
            ChatGPTAgentConfig(
                openai_api_key=openai_api_key,
                initial_message=BaseMessage(text="Hi! I'm your AI assistant with optimized speech recognition. Let's have a conversation!"),
                prompt_preamble="""You are a helpful and friendly AI assistant. Keep responses concise and conversational. 
                Respond naturally as if in a spoken conversation.""",
                model_name="gpt-3.5-turbo",
                generate_responses=True,
            )
        )
    else:
        agent = EchoAgent(
            EchoAgentConfig(
                initial_message=BaseMessage(text="Hello! I'm an echo agent with optimized speech recognition!"),
            )
        )
    
    # 会話の設定
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=OptimizedGoogleSRTranscriber(
            OptimizedGoogleSRTranscriberConfig.from_input_device(
                microphone_input,
                language="en-US",
                energy_threshold=300,
                pause_threshold=0.5,
                chunk_duration_seconds=0.5,
            ),
        ),
        agent=agent,
        synthesizer=GTTSSynthesizer(
            GTTSSynthesizerConfig.from_output_device(
                speaker_output,
                lang="en",
                tld="com",
            ),
        ),
    )
    
    await conversation.start()
    print("🎙️  会話を開始しました！")
    print("💡 ヒント: はっきりと話してください。話し終わったら少し待つと認識されます。")
    print("🛑 終了: Ctrl+C")
    print("-" * 60)
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    print("\n🔧 高性能音声認識システムを初期化中...")
    
    try:
        # マイクテスト
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("✅ マイク: 準備完了")
            r.adjust_for_ambient_noise(source, duration=1)
            print("✅ ノイズレベル: 調整完了")
    except Exception as e:
        print(f"❌ マイクエラー: {e}")
        exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 ご利用ありがとうございました！")